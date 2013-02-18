# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Nova support for guru meditation reports.

This class defines some extra Nova specific guru meditation
report generators and some standard configuration parameters.
"""

from nova.openstack.common import cfg
from nova.openstack.common.gurumed import generator
from nova.openstack.common.gurumed import model
from nova.openstack.common.gurumed import report
from nova import version


class PackageGenerator(generator.Generator):

    def __init__(self):
        super(PackageGenerator,
              self).__init__("Package")

    def get_model(self):
        return model.PackageModel(version.vendor_string(),
                                  version.product_string(),
                                  version.version_string(),
                                  version.package_string())


generator.register(PackageGenerator())


def setup():
    report.autodump()
