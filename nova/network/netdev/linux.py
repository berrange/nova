# Copyright 2014 Red Hat, Inc
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

"""Provides the driver implementation for interacting with network
devices on Linux platforms"""

import os

from nova import exception
from nova import utils
from nova.openstack.common.gettextutils import _
from nova.network.netdev import driver


class LinuxNetDevDriver(driver.NetDevDriver):

    def exists(self, devname):
        return os.path.exists('/sys/class/net/%s' % devname)

    def create_bridge(self, brname):
        utils.execute('brctl', 'addbr', brname, run_as_root=True)

    def delete_bridge(self, brname):
        utils.execute('brctl', 'delbr', brname, run_as_root=True)

    def add_to_bridge(self, brname, devname, ignoreAlreadyAdded=False):
        out, err = utils.execute('brctl', 'addif', brname, devname,
                                 check_exit_code=False, run_as_root=True)

        if err:
            if (ignoreAlreadyAdded and
                err == "device %s is already a member of a bridge;"
                "can't enslave it to bridge %s.\n" % (devname, brname)):
                return

            msg = _('Failed to add interface: %s') % err
            raise exception.NovaException(msg)

    def remove_from_bridge(self, brname, devname):
        utils.execute('brctl', 'delif', brname, devname,
                      run_as_root=True)
