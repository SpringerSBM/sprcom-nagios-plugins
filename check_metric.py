#!/usr/bin/python
# coding=utf-8

"""
Retrieves and checks a metric from graphite.

e.g.
sumSeries(sprcom.services.price-service.live.instance.*.com.kenshoo.play.metrics.MetricsFilter.requestTimer.m15_rate)
"""

from __future__ import print_function

__version__ = "1.0"

import sys
import argparse
import requests
import nagiosplugin

# are we in verbose logging mode?
verbose = False

@nagiosplugin.guarded
class Metric(nagiosplugin.Resource):
    def __init__(self, host, metric, start_time, end_time):
        self.host = host
        self.metric = metric
        self.start_time = start_time
        self.end_time = end_time

    def probe(self):
        metric_json = retrieve_metric(self.host, self.metric, self.start_time, self.end_time)
        for data in metric_json:
            for point in reversed(data['datapoints']):
                if point[0] is not None:
                    return [nagiosplugin.Metric(name=getTargetName(data['target']), value=point[0], context="Metric")]
        # no results available
        return []


def retrieve_metric(host, name, start_time, end_time):
    params = {"target": name, "format": "json", "from": start_time, "until": end_time}
    r = requests.get("http://%s/render" % host, params=params)
    if verbose:
        print("### sent: %s" % r.request.url, file=sys.stderr)
        print("### received status: %s" % r.status_code, file=sys.stderr)
    return r.json()

def getTargetName(target):
    return target.split('.')[-1]


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
o.add_argument('-s', '--start', help="beginning of the time interval within which data is to be retrieved", default="-5min")
o.add_argument('-e', '--end', help="end of the time interval within which data is to be retrieved", default="-90s")
o.add_argument('-V', '--version', action="version", version=__version__)
o.add_argument('-v', '--verbose', action="store_true", help="increase output verbosity")
options = o.parse_args()

# noinspection PyRedeclaration
verbose = options.verbose
nagiosplugin.Check(Metric(options.host, options.metric, options.start, options.end),
                   nagiosplugin.ScalarContext("Metric", options.warning, options.critical)).main()