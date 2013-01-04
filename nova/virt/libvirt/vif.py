# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2011 Midokura KK
# Copyright (C) 2011 Nicira, Inc
# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""VIF drivers for libvirt."""

from copy import deepcopy

from nova import exception
from nova.network import linux_net
from nova.network import model as network_model
from nova.openstack.common import cfg
from nova.openstack.common import log as logging
from nova import utils

from nova.virt import firewall
from nova.virt.libvirt import config as vconfig
from nova.virt.libvirt import designer
from nova.virt import netutils

LOG = logging.getLogger(__name__)

libvirt_vif_opts = [
    cfg.BoolOpt('libvirt_use_virtio_for_bridges',
                default=True,
                help='Use virtio for bridge interfaces with KVM/QEMU'),
]

CONF = cfg.CONF
CONF.register_opts(libvirt_vif_opts)
CONF.import_opt('libvirt_type', 'nova.virt.libvirt.driver')
CONF.import_opt('use_ipv6', 'nova.config')
CONF.import_opt('firewall_driver', 'nova.virt.firewall')

LINUX_DEV_LEN = 14

# Since libvirt 0.9.11, <interface type='bridge'>
# supports OpenVSwitch natively.
LIBVIRT_OVS_VPORT_VERSION = 9011


class LibvirtBaseVIFDriver(object):

    def get_firewall_required(self, instance, network, mapping, conn):
        if CONF.firewall_driver != "nova.virt.firewall.NoopFirewallDriver":
            return True
        return False

    def get_vif_devname(self, mapping):
        if 'vif_devname' in mapping:
            return mapping['vif_devname']
        return ("nic" + mapping['vif_uuid'])[:LINUX_DEV_LEN]

    def get_config(self, instance, network, mapping, conn):
        conf = vconfig.LibvirtConfigGuestInterface()
        model = None
        driver = None
        if CONF.libvirt_type in ('kvm', 'qemu') and \
                CONF.libvirt_use_virtio_for_bridges:
            model = "virtio"
            # Workaround libvirt bug, where it mistakenly
            # enables vhost mode, even for non-KVM guests
            if CONF.libvirt_type == "qemu":
                driver = "qemu"

        designer.set_vif_guest_frontend_config(
            conf, mapping['mac'], model, driver)

        return conf

    def plug(self, instance, vif, conn):
        pass

    def unplug(self, instance, vif, conn):
        pass


class LibvirtGenericVIFDriver(LibvirtBaseVIFDriver):

    def get_br_name(self, iface_id):
        return ("qbr" + iface_id)[:LINUX_DEV_LEN]

    def get_veth_pair_names(self, iface_id):
        return (("qvb%s" % iface_id)[:LINUX_DEV_LEN],
                ("qvo%s" % iface_id)[:LINUX_DEV_LEN])

    def get_config_ovs_ethernet(self, instance, network, mapping, conn):
        conf = super(LibvirtGenericVIFDriver,
                     self).get_config(instance,
                                      network,
                                      mapping,
                                      conn)

        dev = self.get_vif_devname(mapping)
        designer.set_vif_host_backend_ethernet_config(conf, dev)

        return conf

    def get_config_ovs_bridge(self, instance, network, mapping, conn):
        conf = super(LibvirtGenericVIFDriver,
                     self).get_config(instance,
                                      network,
                                      mapping,
                                      conn)

        designer.set_vif_host_backend_ovs_config(
            conf, network['bridge'], mapping['vif_uuid'],
            self.get_vif_devname(mapping))

        return conf

    def get_config_ovs_hybrid(self, instance, network, mapping, conn):
        newnet = deepcopy(network)
        newnet['bridge'] = self.get_br_name(mapping['vif_uuid'])
        return self.get_config_bridge(instance,
                                      newnet,
                                      mapping,
                                      conn)

    def get_config_ovs(self, instance, network, mapping, conn):
        if self.get_firewall_required(instance, network, mapping, conn):
            return self.get_config_ovs_hybrid(instance, network,
                                              mapping, conn)
        elif conn.getLibVersion() >= LIBVIRT_OVS_VPORT_VERSION:
            return self.get_config_ovs_bridge(instance, network,
                                              mapping, conn)
        else:
            return self.get_config_ovs_ethernet(instance, network,
                                                mapping, conn)

    def get_config_bridge(self, instance, network, mapping, conn):
        conf = super(LibvirtGenericVIFDriver,
                     self).get_config(instance,
                                      network,
                                      mapping,
                                      conn)
        mac_id = mapping['mac'].replace(':', '')

        designer.set_vif_host_backend_bridge_config(
            conf, network['bridge'], self.get_vif_devname(mapping))

        name = "nova-instance-" + instance['name'] + "-" + mac_id
        primary_addr = mapping['ips'][0]['ip']
        dhcp_server = ra_server = ipv4_cidr = ipv6_cidr = None

        if mapping['dhcp_server']:
            dhcp_server = mapping['dhcp_server']
        if CONF.use_ipv6:
            ra_server = mapping.get('gateway_v6') + "/128"
        if CONF.allow_same_net_traffic:
            ipv4_cidr = network['cidr']
            if CONF.use_ipv6:
                ipv6_cidr = network['cidr_v6']

        designer.set_vif_host_backend_filter_config(
            conf, name, primary_addr, dhcp_server,
            ra_server, ipv4_cidr, ipv6_cidr)

        return conf

    def get_config_802qbg(self, instance, network, mapping, conn):
        conf = super(LibvirtGenericVIFDriver,
                     self).get_config(instance,
                                      network,
                                      mapping,
                                      conn)
        raise NotImplementedError()

    def get_config_802qbh(self, instance, network, mapping, conn):
        conf = super(LibvirtGenericVIFDriver,
                     self).get_config(instance,
                                      network,
                                      mapping,
                                      conn)
        raise NotImplementedError()

    def get_config(self, instance, network, mapping, conn):
        vif_type = mapping['vif_type']

        LOG.debug(_("vif_type=%(vif_type)s instance=%(instance)s "
                    "network=%(network)s mapping=%(mapping)s")
                  % locals())

        if vif_type is None:
            raise NovaException(_("vif_type parameter must be present "
                                  "for this vif_driver implementation"))

        if vif_type == network_model.VIF_TYPE_OVS:
            return self.get_config_ovs(instance, network, mapping, conn)
        elif vif_type == network_model.VIF_TYPE_BRIDGE:
            return self.get_config_bridge(instance, network, mapping, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBG:
            return self.get_config_802qbg(instance, network, mapping, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBH:
            return self.get_config_802qbh(instance, network, mapping, conn)
        else:
            raise NovaException(_("Unexpected vif_type=%s") % vif_type)

    def plug_ovs_ethernet(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        network, mapping = vif
        iface_id = mapping['vif_uuid']
        dev = self.get_vif_devname(mapping)
        linux_net.create_tap_dev(dev)
        linux_net.create_ovs_vif_port(network['bridge'],
                                      dev, iface_id, mapping['mac'],
                                      instance['uuid'])

    def plug_ovs_bridge(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

    def plug_ovs_hybrid(self, instance, vif, conn):
        """Plug using hybrid strategy

        Create a per-VIF linux bridge, then link that bridge to the OVS
        integration bridge via a veth device, setting up the other end
        of the veth device just like a normal OVS port.  Then boot the
        VIF on the linux bridge using standard libvirt mechanisms
        """
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        network, mapping = vif
        iface_id = mapping['vif_uuid']
        br_name = self.get_br_name(iface_id)
        v1_name, v2_name = self.get_veth_pair_names(iface_id)

        if not linux_net.device_exists(br_name):
            utils.execute('brctl', 'addbr', br_name, run_as_root=True)

        if not linux_net.device_exists(v2_name):
            linux_net._create_veth_pair(v1_name, v2_name)
            utils.execute('ip', 'link', 'set', br_name, 'up', run_as_root=True)
            utils.execute('brctl', 'addif', br_name, v1_name, run_as_root=True)
            linux_net.create_ovs_vif_port(network['bridge'],
                                          v2_name, iface_id, mapping['mac'],
                                          instance['uuid'])

    def plug_ovs(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        network, mapping = vif
        if self.get_firewall_required(instance, network, mapping, conn):
            self.plug_ovs_hybrid(instance, vif, conn)
        elif conn.getLibVersion() >= LIBVIRT_OVS_VPORT_VERSION:
            self.plug_ovs_bridge(instance, vif, conn)
        else:
            self.plug_ovs_ethernet(instance, vif, conn)

    def plug_bridge(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        network, mapping = vif
        if (not network.get('multi_host') and
            mapping.get('should_create_bridge')):
            if mapping.get('should_create_vlan'):
                iface = CONF.vlan_interface or network['bridge_interface']
                LOG.debug(_('Ensuring vlan %(vlan)s and bridge %(bridge)s'),
                          {'vlan': network['vlan'],
                           'bridge': network['bridge']},
                          instance=instance)
                linux_net.LinuxBridgeInterfaceDriver.ensure_vlan_bridge(
                                             network['vlan'],
                                             network['bridge'],
                                             iface)
            else:
                iface = CONF.flat_interface or network['bridge_interface']
                LOG.debug(_("Ensuring bridge %s"), network['bridge'],
                          instance=instance)
                linux_net.LinuxBridgeInterfaceDriver.ensure_bridge(
                                        network['bridge'],
                                        iface)

    def plug_802qbg(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        raise NotImplementedError()

    def plug_802qbh(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).plug(instance, vif, conn)

        raise NotImplementedError()

    def plug(self, instance, vif, conn):
        network, mapping = vif
        vif_type = mapping['vif_type']

        LOG.debug(_("vif_type=%(vif_type)s instance=%(instance)s "
                    "network=%(network)s mapping=%(mapping)s")
                  % locals())

        if vif_type is None:
            raise NovaException(_("vif_type parameter must be present "
                                  "for this vif_driver implementation"))

        if vif_type == network_model.VIF_TYPE_OVS:
            self.plug_ovs(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_BRIDGE:
            self.plug_bridge(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBG:
            self.plug_802qbg(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBH:
            self.plug_802qbh(instance, vif, conn)
        else:
            raise NovaException(_("Unexpected vif_type=%s") % vif_type)

    def unplug_ovs_ethernet(self, instance, vif, conn):
        """Unplug the VIF by deleting the port from the bridge."""
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)
        try:
            network, mapping = vif
            linux_net.delete_ovs_vif_port(network['bridge'],
                                          self.get_vif_devname(mapping))
        except exception.ProcessExecutionError:
            LOG.exception(_("Failed while unplugging vif"), instance=instance)

    def unplug_ovs_bridge(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

    def unplug_ovs_hybrid(self, instance, vif, conn):
        """UnPlug using hybrid strategy

        Unhook port from OVS, unhook port from bridge, delete
        bridge, and delete both veth devices.
        """
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

        try:
            network, mapping = vif
            iface_id = mapping['vif_uuid']
            br_name = self.get_br_name(iface_id)
            v1_name, v2_name = self.get_veth_pair_names(iface_id)

            utils.execute('brctl', 'delif', br_name, v1_name, run_as_root=True)
            utils.execute('ip', 'link', 'set', br_name, 'down',
                          run_as_root=True)
            utils.execute('brctl', 'delbr', br_name, run_as_root=True)

            linux_net.delete_ovs_vif_port(network['bridge'], v2_name)
        except exception.ProcessExecutionError:
            LOG.exception(_("Failed while unplugging vif"), instance=instance)

    def unplug_ovs(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

        network, mapping = vif
        if self.get_firewall_required(instance, network, mapping, conn):
            self.unplug_ovs_hybrid(instance, vif, conn)
        elif conn.getLibVersion() >= LIBVIRT_OVS_VPORT_VERSION:
            self.unplug_ovs_bridge(instance, vif, conn)
        else:
            self.unplug_ovs_ethernet(instance, vif, conn)

    def unplug_bridge(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

    def unplug_802qbg(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

        raise NotImplementedError()

    def unplug_802qbh(self, instance, vif, conn):
        super(LibvirtGenericVIFDriver,
              self).unplug(instance, vif, conn)

        raise NotImplementedError()

    def unplug(self, instance, vif, conn):
        network, mapping = vif
        vif_type = mapping['vif_type']

        LOG.debug(_("vif_type=%(vif_type)s instance=%(instance)s "
                    "network=%(network)s mapping=%(mapping)s")
                  % locals())

        if vif_type is None:
            raise NovaException(_("vif_type parameter must be present "
                                  "for this vif_driver implementation"))

        if vif_type == network_model.VIF_TYPE_OVS:
            self.unplug_ovs(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_BRIDGE:
            self.unplug_bridge(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBG:
            self.unplug_802qbg(instance, vif, conn)
        elif vif_type == network_model.VIF_TYPE_802_QBH:
            self.unplug_802qbh(instance, vif, conn)
        else:
            raise NovaException(_("Unexpected vif_type=%s") % vif_type)


class LibvirtBridgeDriver(LibvirtGenericVIFDriver):
    """Obsoleted by LibvirtGenericVIFDriver. Retained for Grizzly to
       facilitate migration to new impl. To be removed in Hxxxx"""

    def __init__(self):
        LOG.warn("LibvirtBridgeDriver is obsolete. " +
                 "Update the libvirt_vif_driver config parameter " +
                 "to use the LibvirtGenericVIFDriver class instead")

    def get_config(self, instance, network, mapping, conn):
        return self.get_config_bridge(instance, network, mapping, conn)

    def plug(self, instance, vif, conn):
        return self.plug_bridge(instance, vif, conn)

    def unplug(self, instance, vif, conn):
        return self.unplug_bridge(instance, vif, conn)


class LibvirtOpenVswitchDriver(LibvirtGenericVIFDriver):
    """Obsoleted by LibvirtGenericVIFDriver. Retained for Grizzly to
       facilitate migration to new impl. To be removed in Hxxxx"""

    def __init__(self):
        LOG.warn("LibvirtOpenVswitchDriver is obsolete. " +
                 "Update the libvirt_vif_driver config parameter " +
                 "to use the LibvirtGenericVIFDriver class instead")

    def get_config(self, instance, network, mapping, conn):
        return self.get_config_ovs_ethernet(instance, network, mapping, conn)

    def plug(self, instance, vif, conn):
        return self.plug_ovs_ethernet(instance, vif, conn)

    def unplug(self, instance, vif, conn):
        return self.unplug_ovs_ethernet(instance, vif, conn)


class LibvirtHybridOVSBridgeDriver(LibvirtGenericVIFDriver):
    """Obsoleted by LibvirtGenericVIFDriver. Retained for Grizzly to
       facilitate migration to new impl. To be removed in Hxxxx"""

    def __init__(self):
        LOG.warn("LibvirtHybridOVSBridgeDriver is obsolete. " +
                 "Update the libvirt_vif_driver config parameter " +
                 "to use the LibvirtGenericVIFDriver class instead")

    def get_config(self, instance, network, mapping, conn):
        return self.get_config_ovs_hybrid(instance, network, mapping, conn)

    def plug(self, instance, vif, conn):
        return self.plug_ovs_hybrid(instance, vif, conn)

    def unplug(self, instance, vif, conn):
        return self.unplug_ovs_hybrid(instance, vif, conn)


class LibvirtOpenVswitchVirtualPortDriver(LibvirtGenericVIFDriver):
    """Obsoleted by LibvirtGenericVIFDriver. Retained for Grizzly to
       facilitate migration to new impl. To be removed in Hxxxx"""

    def __init__(self):
        LOG.warn("LibvirtOpenVswitchVirtualPortDriver is obsolete. " +
                 "Update the libvirt_vif_driver config parameter " +
                 "to use the LibvirtGenericVIFDriver class instead")

    def get_config(self, instance, network, mapping, conn):
        return self.get_config_ovs_bridge(instance, network, mapping, conn)

    def plug(self, instance, vif, conn):
        return self.plug_ovs_bridge(instance, vif, conn)

    def unplug(self, instance, vif, conn):
        return self.unplug_ovs_bridge(instance, vif, conn)


class QuantumLinuxBridgeVIFDriver(LibvirtGenericVIFDriver):
    """Obsoleted by LibvirtGenericVIFDriver. Retained for Grizzly to
       facilitate migration to new impl. To be removed in Hxxxx"""

    def __init__(self):
        LOG.warn("QuantumLinuxBridgeVIFDriver is obsolete. " +
                 "Update the libvirt_vif_driver config parameter " +
                 "to use the LibvirtGenericVIFDriver class instead")

    def get_config(self, instance, network, mapping, conn):
        return self.get_config_bridge(instance, network, mapping, conn)

    def plug(self, instance, vif, conn):
        return self.plug_bridge(instance, vif, conn)

    def unplug(self, instance, vif, conn):
        return self.unplug_bridge(instance, vif, conn)
