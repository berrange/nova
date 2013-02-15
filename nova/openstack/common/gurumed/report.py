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
Provides public APIs for generating guru meditation reports

This module provides the public APIs required to generate
guru meditation error reports
"""

import signal
import sys

from nova.openstack.common.gurumed import generator


FORMAT_TEXT = "txt"
FORMAT_XML = "xml"
FORMAT_JSON = "json"


def create(fmt=FORMAT_TEXT):
    """Create a new guru meditation report.

    Create a new guru meditation report, convert
    it to the requested format and return a string
    with the resulting text."""

    report = generator.create_report()
    if fmt == FORMAT_TEXT:
        return str(report)
    elif fmt == FORMAT_JSON:
        return jsonutils.dumps(report)
    else:
        raise Exception("Unknown format %s" % fmt)


def save(dirname, filename=None, fmt=FORMAT_TEXT):
    """Save a new guru meditation report to a file.

    Create a new guru meditation report, saving it
    to the specified directory. If filename is left
    as None, then the filename will be generated based
    on the report UUID."""

    report = create(fmt)

    if filename is None:
        uuid = report["uuid"]
        filename = "gurumed-%(uuid)s.%(fmt)s" % locals()

    path = os.path.join(dirname, filename)

    f = open(path, "w+")
    f.write(report)
    f.close()


def dump(fmt=FORMAT_TEXT):
    """Dump a new guru meditation report to the console.

    Create a new guru meditation report, dumping it
    to stderr in the specified format."""

    report = create(fmt)

    print >> sys.stderr, report


def __handle_signal(*args):
    try:
        dump()
    except Exception, e:
        print >> sys.stderr, "Failed to dump guru meditation report %s" % e


def autodump(signum=signal.SIGUSR1):
    """Register a signal handler to trigger a report.

    Register a signal handler that will dump a new
    guru meditation report to stderr when triggered."""

    signal.signal(signum, __handle_signal)
