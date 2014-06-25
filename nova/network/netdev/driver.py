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

"""Defines a low level driver API contract for interacting with
network devices in a platform agnostic manner"""

class NetDevDriver(object):

    def exists(self, devname):
        raise NotImplementedError("%s does not implement 'exists'" %
                                  type(self))

    def create_bridge(self, brname):
        raise NotImplementedError("%s does not implement 'create_bridge'" %
                                  type(self))

    def delete_bridge(self, brname):
        raise NotImplementedError("%s does not implement 'delete_bridge'" %
                                  type(self))

    def add_to_bridge(self, brname, devname, ignoreAlreadyAdded=False):
        raise NotImplementedError("%s does not implement 'add_to_bridge'" %
                                  type(self))

    def remove_from_bridge(self, brname, devname):
        raise NotImplementedError("%s does not implement 'remove_from_bridge'" %
                                  type(self))
