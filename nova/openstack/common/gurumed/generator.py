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
Data generators for guru meditation reports

This module provides a framework for generating data for sections
in a guru meditation report.
"""

import gc
import greenlet
import sys
import traceback

import nova.openstack.common.cfg as cfg

import nova.openstack.common.gurumed.model as model

generators = []

def register(generator):
    """Register a new generator implementation.

    Register a new generator class for providing
    custom data in a guru meditation report."""

    generators.append(generator)


def create_report():
    """Create a new guru meditation report.

    Returns an instance of the ReportModel class representing
    a new guru meditation report."""

    sections = []
    for generator in generators:
        data = generator.get_model()
        title = generator.get_title()
        if data is not None:
            sections.append(model.SectionModel(title, data))
    return model.ReportModel(sections)


class Generator(object):

    def __init__(self, title):

        self._title = title

    def get_title(self):
        return self._title

    def get_model(self):
        raise NotImplementedError()


class NativeThreadGenerator(Generator):

    def __init__(self):
        super(NativeThreadGenerator,
              self).__init__("Native threads")

    def get_model(self):
        threads = []
        for threadId, stack in sys._current_frames().items():
            thread = model.ThreadModel(threadId, stack)
            threads.append(thread)

        if len(threads) == 0:
            return None
        return model.ThreadListModel(threads)


class GreenThreadGenerator(Generator):

    def __init__(self):
        super(GreenThreadGenerator,
              self).__init__("Green threads")

    def get_model(self):
        def _find_objects(t):
            return filter(lambda o: isinstance(o, t), gc.get_objects())

        threads = []
        for i, gt in enumerate(_find_objects(greenlet.greenlet)):
            thread = model.ThreadModel(i, gt.gr_frame)
            threads.append(thread)

        if len(threads) == 0:
            return None
        return model.ThreadListModel(threads)


class ExceptionGenerator(Generator):

    def __init__(self):
        super(ExceptionGenerator,
              self).__init__("Exception")

    def get_model(self):
        (type, value, traceback) = sys.exc_info()
        if value is None:
            return None
        return model.ExceptionModel(value, traceback)


class ConfigGenerator(Generator):

    def __init__(self):
        super(ConfigGenerator,
              self).__init__("Config")

    def get_model(self):
        return model.ConfigModel(cfg.CONF)


register(ConfigGenerator())
register(ExceptionGenerator())
register(NativeThreadGenerator())
register(GreenThreadGenerator())
