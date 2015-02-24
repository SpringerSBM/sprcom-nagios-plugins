#!/usr/bin/python
# coding=utf-8

"""
Checks the time of the most recent successful chef-client run
knife status "hostname:sprcom-dev-01"
2 hours ago, sprcom-services-dev-01, sprcom-dev-01.springer-sbm.com, 10.9.0.65, centos 6.5.
"""

from __future__ import print_function

__version__ = "1.0"

import subprocess
import argparse
import nagiosplugin
import sys


@nagiosplugin.guarded
class ChefClient(nagiosplugin.Resource):
    def __init__(self, hostname):
        self.hostname = hostname

    def probe(self):
        for line in getNodeStatus(self.hostname):
            if line is not None:
                return [nagiosplugin.Metric(name='chef-client run', value=getLastUpdate(line), context="chef_client")]
        # no results available
        return []

def getNodeStatus(hostname):
    process = subprocess.Popen(getKnifeStatusCommand(hostname), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return process.stdout.readlines()

def getLastUpdate(statusLine):
    if verbose:
        print("### statusLine: %s" % statusLine, file=sys.stderr)
    return int(statusLine.split().pop(0))

def getKnifeStatusCommand(hostname):
    command = ("/usr/bin/knife status hostname:%s -c /etc/chef/client.rb" % hostname).split()
    if verbose:
        print("### command: %s" % command, file=sys.stderr)
    return command

range_desc = """
supports nagios-style ranges. The general format is “[@][start:][end]”. “start:” may be omitted if start==0.
“~:” means that start is negative infinity. If end is omitted, infinity is assumed.
To invert the match condition, prefix the range expression with “@”.
"""

o = argparse.ArgumentParser(description=__doc__)
o.add_argument('-H', '--hostname', help="hostname of the chef node", required=True)
o.add_argument('-w', '--warning', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-c', '--critical', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-V', '--version', action="version", version=__version__)
o.add_argument('-v', '--verbose', action="store_true", help="increase output verbosity")
options = o.parse_args()


# noinspection PyRedeclaration
verbose = options.verbose
nagiosplugin.Check(ChefClient(options.hostname),
                   nagiosplugin.ScalarContext("chef_client", options.warning, options.critical)).main()
