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

"""Provides a set of low level APIs for interacting with network
devices in a platform agnostic manner"""

import os

from nova.openstack.common.gettextutils import _

from nova.network.netdev import driver
from nova.network.netdev import linux

driverObj = None

def get_driver():
    global driverObj
    if driverObj is None:
        if os.uname()[0] == "Linux":
            driverObj = linux.LinuxNetDevDriver()
        else:
            raise NotImplementedError(_("netdev driver has not been ported to '%s'") %
                                      os.uname()[0])

        driverObj = driver.NetDevDriver.get_instance()
    return driverObj

def exists(devname):
    return get_driver().exists(devname)

def create_bridge(brname):
    return get_driver().create_bridge(brname)

def delete_bridge(brname):
    return get_driver().delete_bridge(brname)

def add_to_bridge(brname, devname, ignoreAlreadyAdded=False):
    return get_driver().add_to_bridge(brname, devname)

def remove_from_bridge(brname, devname):
    return get_driver().remove_from_bridge(brname, devname)
