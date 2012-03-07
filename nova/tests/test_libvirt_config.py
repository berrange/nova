# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#    Copyright (C) 2012 Red Hat, Inc.
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

from lxml import etree

from nova import test

from nova.virt.libvirt import config

class LibvirtConfigTest(test.TestCase):

    def test_config_plain(self):
        obj = config.LibvirtConfigObject(rootname="demo")
        xml = obj.to_xml()

        self.assertEqual(xml, "<demo/>\n")


    def test_config_ns(self):
        obj = config.LibvirtConfigObject(rootname="demo", ns_prefix="foo", ns_uri="http://example.com/foo")
        xml = obj.to_xml()

        self.assertEqual(xml, "<foo:demo xmlns:foo=\"http://example.com/foo\"/>\n")

    def test_config_text(self):
        obj = config.LibvirtConfigObject(rootname="demo")
        root = obj.format_dom()
        root.append(obj._text_node("foo", "bar"))

        xml = etree.tostring(root)
        self.assertEqual(xml, "<demo><foo>bar</foo></demo>");


class LibvirtConfigGuestDiskTest(test.TestCase):

    def test_config_file(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<disk type="file" device="disk">
  <source file="/tmp/hello"/>
  <target bus="ide" dev="/dev/hda"/>
</disk>
""")

    def test_config_block(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "block"
        obj.source_path = "/tmp/hello"
        obj.source_device = "cdrom"
        obj.driver_name = "qemu"
        obj.target_dev = "/dev/hdc"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<disk type="block" device="cdrom">
  <driver name="qemu"/>
  <source dev="/tmp/hello"/>
  <target bus="ide" dev="/dev/hdc"/>
</disk>
""")

    def test_config_network(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "network"
        obj.source_protocol = "iscsi"
        obj.source_host = "foo.bar.com"
        obj.driver_name = "qemu"
        obj.driver_format = "qcow2"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<disk type="network" device="disk">
  <driver name="qemu" type="qcow2"/>
  <source protocol="iscsi" name="foo.bar.com"/>
  <target bus="ide" dev="/dev/hda"/>
</disk>
""")


class LibvirtConfigGuestFilesysTest(test.TestCase):

    def test_config_mount(self):
        obj = config.LibvirtConfigGuestFilesys()
        obj.source_type = "mount"
        obj.source_dir = "/tmp/hello"
        obj.target_dir = "/mnt"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<filesystem type="mount">
  <source dir="/tmp/hello"/>
  <target dir="/mnt"/>
</filesystem>
""")

class LibvirtConfigGuestInputTest(test.TestCase):

    def test_config_tablet(self):
        obj = config.LibvirtConfigGuestInput()

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<input type="tablet" bus="usb"/>
""")


class LibvirtConfigGuestGraphicsTest(test.TestCase):

    def test_config_tablet(self):
        obj = config.LibvirtConfigGuestGraphics()
        obj.type = "vnc"
        obj.autoport = True
        obj.keymap = "en_US"
        obj.listen = "127.0.0.1"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<graphics type="vnc" autoport="yes" keymap="en_US" listen="127.0.0.1"/>
""")


class LibvirtConfigGuestSerialTest(test.TestCase):

    def test_config_file(self):
        obj = config.LibvirtConfigGuestSerial()
        obj.type = "file"
        obj.source_path = "/tmp/vm.log"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<serial type="file">
  <source file="/tmp/vm.log"/>
</serial>
""")


class LibvirtConfigGuestSerialTest(test.TestCase):
    def test_config_pty(self):
        obj = config.LibvirtConfigGuestConsole()
        obj.type = "pty"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<console type="pty"/>
""")



class LibvirtConfigGuestInterfaceTest(test.TestCase):
    def test_config_ethernet(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "ethernet"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.target_dev = "vnet0"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<interface type="ethernet">
  <mac address="DE:AD:BE:EF:CA:FE"/>
  <model type="virtio"/>
  <target dev="vnet0"/>
</interface>
""")


    def test_config_bridge(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "bridge"
        obj.source_dev = "br0"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.filtername = "clean-traffic"
        obj.filterparams.append({"key": "IP", "value": "192.168.122.1"})

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<interface type="bridge">
  <mac address="DE:AD:BE:EF:CA:FE"/>
  <model type="virtio"/>
  <source bridge="br0"/>
  <filterref filter="clean-traffic">
    <parameter name="IP" value="192.168.122.1"/>
  </filterref>
</interface>
""")


    def test_config_bridge_ovs(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "bridge"
        obj.source_dev = "br0"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.vporttype = "openvswitch"
        obj.vportparams.append({"key": "instanceid", "value":"foobar"})

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<interface type="bridge">
  <mac address="DE:AD:BE:EF:CA:FE"/>
  <model type="virtio"/>
  <source bridge="br0"/>
  <virtualport type="openvswitch">
    <parameters instanceid="foobar"/>
  </virtualport>
</interface>
""")


    def test_config_8021Qbh(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "direct"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.source_dev = "eth0"
        obj.vporttype = "802.1Qbh"

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<interface type="direct">
  <mac address="DE:AD:BE:EF:CA:FE"/>
  <model type="virtio"/>
  <source mode="private" dev="eth0"/>
  <virtualport type="802.1Qbh"/>
</interface>
""")




class LibvirtConfigGuestTest(test.TestCase):

    def test_config_lxc(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "lxc"
        obj.memory = 1024*1024*100
        obj.vcpus = 2
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "exe"
        obj.os_init_path = "/sbin/init"

        fs = config.LibvirtConfigGuestFilesys()
        fs.source_dir = "/root/lxc"
        fs.target_dir = "/"

        obj.add_device(fs)

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<domain type="lxc">
  <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
  <name>demo</name>
  <memory>104857600</memory>
  <vcpu>2</vcpu>
  <os>
    <type>exe</type>
    <init>/sbin/init</init>
  </os>
  <devices>
    <filesystem type="mount">
      <source dir="/root/lxc"/>
      <target dir="/"/>
    </filesystem>
  </devices>
</domain>
""")


    def test_config_xen(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "xen"
        obj.memory = 1024*1024*100
        obj.vcpus = 2
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "linux"
        obj.os_kernel = "/tmp/vmlinuz"
        obj.os_initrd = "/tmp/ramdisk"
        obj.os_root = "root=xvda"
        obj.os_cmdline = "console=xvc0"

        disk = config.LibvirtConfigGuestDisk()
        disk.source_type = "file"
        disk.source_path = "/tmp/img"
        disk.target_dev = "/dev/xvda"
        disk.target_bus = "xen"

        obj.add_device(disk)

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<domain type="xen">
  <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
  <name>demo</name>
  <memory>104857600</memory>
  <vcpu>2</vcpu>
  <os>
    <type>linux</type>
    <kernel>/tmp/vmlinuz</kernel>
    <initrd>/tmp/ramdisk</initrd>
    <cmdline>console=xvc0</cmdline>
    <root>root=xvda</root>
  </os>
  <devices>
    <disk type="file" device="disk">
      <source file="/tmp/img"/>
      <target bus="xen" dev="/dev/xvda"/>
    </disk>
  </devices>
</domain>
""")

    def test_config_kvm(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "kvm"
        obj.memory = 1024*1024*100
        obj.vcpus = 2
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "linux"
        obj.os_boot_dev = "hd"

        disk = config.LibvirtConfigGuestDisk()
        disk.source_type = "file"
        disk.source_path = "/tmp/img"
        disk.target_dev = "/dev/vda"
        disk.target_bus = "virtio"

        obj.add_device(disk)

        xml = obj.to_xml()
        self.assertEqual(xml,
"""<domain type="kvm">
  <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
  <name>demo</name>
  <memory>104857600</memory>
  <vcpu>2</vcpu>
  <os>
    <type>linux</type>
    <boot dev="hd"/>
  </os>
  <devices>
    <disk type="file" device="disk">
      <source file="/tmp/img"/>
      <target bus="virtio" dev="/dev/vda"/>
    </disk>
  </devices>
</domain>
""")
