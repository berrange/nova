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
Provides data models for information reported in a guru meditation.

This class defines a set of data models for common information
reported in a guru meditation report. Each class covers a specific
area of functionality. These classes are to be used by the various
error report generators.
"""

import time
import traceback

from nova.openstack.common import cfg
from nova.openstack.common import uuidutils

class Model(dict):
    """Base class for data items included in a report."""


class StackTraceModel(Model):
    """A model describing a stack trace.

    The stack trace model represents the data associated
    with the python 'traceback' or 'frame' objects. It
    provides a list of stack frames, each providing a
    filename, line number, function name and code snippet.
    It is a base for exception or thread models."""

    def __init__(self, stacktrace):

        self["frames"] = []
        if type(stacktrace).__name__ == "traceback":
            tb = traceback.extract_tb(stacktrace)
        else:
            tb = traceback.extract_stack(stacktrace)

        for tbentry in tb:
            frame = {
                "filename": tbentry[0],
                "lineno": tbentry[1],
                "funcname": tbentry[2],
                "text": tbentry[3],
                }
            self["frames"].append(frame)

        self["frames"].reverse()


class ThreadModel(StackTraceModel):
    """A model describing a thread.

    The thread model represents either a green or native
    thread. It extends the StackTraceModel model to provide
    a trace of of the thread's current execution point, and
    adds unique identifier for the thread."""

    def __init__(self, threadid, stacktrace):
        super(ThreadModel,
              self).__init__(stacktrace)

        self["threadid"] = threadid


class ThreadListModel(Model):
    """A model describing a list of threads.

    The thread list model represents either the set of
    green or native threads in the interpretor."""

    def __init__(self, threads):
        self["threads"] = threads


class ExceptionModel(StackTraceModel):
    """A model describing an exception.

    The exception model represents a raised exception.
    It extends teh StackTraceModel model to provide
    a trace of the exception callback, and adds in the
    exception class / message / arg details."""

    def __init__(self, ex, stacktrace):
        super(ExceptionModel,
              self).__init__(stacktrace)

        self["class"] = type(ex).__name__
        self["message"] = ex.message
        self["args"] = ex.args


class ConfigModel(Model):
    """A model describing configuration parameters.

    The config model represents the configuration
    parameters that have been loaded for a interpretor.
    The parameters are partitioned into groups, only
    parameters which are set to non-default values will
    be represented."""

    def __init__(self, options):

        self["groups"] = {
            "DEFAULT": {}
            }

        for option in options:
            value = options.get(option, None)

            if isinstance(value, cfg.ConfigOpts.GroupAttr):
                self["groups"][option] = {}
                for suboption in value:
                    subvalue = value.get(suboption)
                    self["groups"][option][suboption] = str(subvalue)
            else:
                self["groups"]["DEFAULT"][option] = str(value)


class PackageModel(Model):
    """A model describing the package release.

    The package model describes the package name, version
    and release details."""

    def __init__(self, vendor, product, version, package):
        self["vendor"] = vendor
        self["product"] = product
        self["version"] = version
        self["package"] = package


class SectionModel(Model):
    """A model providing a section.

    The section model allows data to be split into a
    number of distinct areas."""

    def __init__(self, title, data):
        self["title"] = title
        self["data"] = data


class ReportModel(Model):
    """A model representing a single guru meditation report.

    The report model provides a list of sections and
    a unique identifier for the report."""

    def __init__(self, sections):
        self["sections"] = sections
        self["uuid"] = uuidutils.generate_uuid()
        self["time"] = time.time()
