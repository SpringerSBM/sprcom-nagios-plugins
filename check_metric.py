"""Retrieves and checks a metric from graphite."""

__version__ = "1.0"

import argparse
import requests
import nagiosplugin


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
    params = {"target": name, "format": "json", "from": "-5min"}
    return requests.get("http://%s/render" % host, params=params).json()


o = argparse.ArgumentParser(description=__doc__)

o.add_argument('-m', '--metric', help="name of the graphite metric to check", required=True)
o.add_argument('-H', '--host', help="name of the graphite host", required=True)
o.add_argument('-w', '--warning', metavar='RANGE', help="(supports nagios-style ranges)", required=True)
o.add_argument('-c', '--critical', metavar='RANGE', help="(supports nagios-style ranges)", required=True)
o.add_argument('-V', '--version', action="version", version=__version__)
options = o.parse_args()

nagiosplugin.Check(Graphite(options.host, options.metric),
                   nagiosplugin.ScalarContext("Graphite", options.warning, options.critical)).main()