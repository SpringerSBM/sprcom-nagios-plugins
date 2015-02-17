#!/usr/bin/python
# coding=utf-8

"""Retrieves and checks a metric from graphite."""

from __future__ import print_function

__version__ = "1.0"

import sys
import argparse
import requests
import nagiosplugin

# are we in verbose logging mode?
verbose = False

@nagiosplugin.guarded
class Graphite(nagiosplugin.Resource):
    def __init__(self, host, metric):
        self.host = host
        self.metric = metric

    def probe(self):
        metric_json = retrieve_metric(self.host, self.metric)
        for data in metric_json:
            for point in reversed(data['datapoints']):
                if point[0] is not None:
                    return [nagiosplugin.Metric(name=data['target'].split('.')[-1], value=point[0], context="Graphite")]
        # no results available
        return []


def retrieve_metric(host, name):
    params = {"target": name, "format": "json", "from": "-5min", "until": "-90s"}
    r = requests.get("http://%s/render" % host, params=params)
    if verbose:
        print("### sent: %s" % r.request.url, file=sys.stderr)
        print("### received status: %s" % r.status_code, file=sys.stderr)
    return r.json()


range_desc = """
supports nagios-style ranges. The general format is “[@][start:][end]”. “start:” may be omitted if start==0.
“~:” means that start is negative infinity. If end is omitted, infinity is assumed.
To invert the match condition, prefix the range expression with “@”.
"""

o = argparse.ArgumentParser(description=__doc__)
o.add_argument('-m', '--metric', help="name of the graphite metric to check", required=True)
o.add_argument('-H', '--host', help="name of the graphite host", required=True)
o.add_argument('-w', '--warning', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-c', '--critical', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-V', '--version', action="version", version=__version__)
o.add_argument('-v', '--verbose', action="store_true", help="increase output verbosity")
options = o.parse_args()

# noinspection PyRedeclaration
verbose = options.verbose
nagiosplugin.Check(Graphite(options.host, options.metric),
                   nagiosplugin.ScalarContext("Graphite", options.warning, options.critical)).main()