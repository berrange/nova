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

import contextlib
import mock
import os.path

from nova import exception
from nova import test
from nova import utils

from nova.network import netdev

class LinuxNetDevDriverTest(test.NoDBTestCase):

    def setUp(self):
        super(LinuxNetDevDriverTest, self).setUp()

    def test_exists(self):
        with contextlib.nested(
                mock.patch.object(os.path, 'exists', return_value=True),
                mock.patch.object(os, 'uname', return_value=('Linux', None, None, None, None)),
        ) as (mock_exists, mock_uname):
            res = netdev.exists("eth0")
            mock_exists.assert_called_once()
            mock_exists.assert_called_once_with(
                "/sys/class/net/eth0"
            )
            self.assertTrue(res)

    def test_create_bridge(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(None, None)),
                mock.patch.object(os, 'uname', return_value=('Linux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            netdev.create_bridge("br0")

            mock_execute.assert_called_once_with(
                "brctl", "addbr", "br0",
                run_as_root=True,
            )

    def test_delete_bridge(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(None, None)),
                mock.patch.object(os, 'uname', return_value=('Linux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            netdev.delete_bridge("br0")

            mock_execute.assert_called_once_with(
                "brctl", "delbr", "br0",
                run_as_root=True,
            )

    def test_add_to_bridge(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(None, None)),
                mock.patch.object(os, 'uname', return_value=('Linux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            netdev.add_to_bridge("br0", "eth0")

            mock_execute.assert_called_once_with(
                "brctl", "addif", "br0", "eth0",
                run_as_root=True, check_exit_code=False,
            )

    def test_add_to_bridge_fail_already_added(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(
                    None,
                    "device eth0 is already a member of a bridge;"
                    "can't enslave it to bridge br0.\n")),
                mock.patch.object(os, 'uname', return_value=('Lindux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            self.assertRaises(exception.NovaException,
                              netdev.add_to_bridge,
                              "br0", "eth0")

            mock_execute.assert_called_once_with(
                "brctl", "addif", "br0", "eth0",
                run_as_root=True, check_exit_code=False,
            )

    def test_add_to_bridge_pass_already_added(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(
                    None,
                    "device eth0 is already a member of a bridge;"
                    "can't enslave it to bridge br0.\n")),
                mock.patch.object(os, 'uname', return_value=('Lindux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            netdev.add_to_bridge("br0", "eth0", ignoreAlreadyAdded=True)

            mock_execute.assert_called_once_with(
                "brctl", "addif", "br0", "eth0",
                run_as_root=True, check_exit_code=False,
            )

    def test_remove_from_bridge(self):
        with contextlib.nested(
                mock.patch.object(utils, 'execute', return_value=(None, None)),
                mock.patch.object(os, 'uname', return_value=('Lindux', None, None, None, None)),
        ) as (mock_execute, mock_uname):
            netdev.remove_from_bridge("br0", "eth0")

            mock_execute.assert_called_once_with(
                "brctl", "delif", "br0", "eth0",
                run_as_root=True,
            )
