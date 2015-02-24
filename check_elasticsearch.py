#!/usr/bin/python
# coding=utf-8

"""Retrieves and checks a metric from elasticsearch."""

from __future__ import print_function

__version__ = "1.0"

import sys
import argparse
import requests
import json
import nagiosplugin

# are we in verbose logging mode?
verbose = False

@nagiosplugin.guarded
class ElasticSearch(nagiosplugin.Resource):
    def __init__(self, host, query, start_time, end_time):
        self.host = host
        self.query = query
        self.start_time = start_time
        self.end_time = end_time

    def probe(self):
        metric = query_elasticsearch(self.host, self.query, self.start_time, self.end_time)
        return [nagiosplugin.Metric(name="es_metric", value=metric, context="ElasticSearch")]

def query_elasticsearch(host, query, start_time, end_time):
    es_query = {
        "query": {
            "filtered": {
                "filter": {
                    "and": [
                        {
                            "query": {
                                "query_string": {
                                    "query": query
                                }
                            }
                        },
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time,
                                    "lt": end_time
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    r = requests.post("http://%s/logstash*/_search?search_type=count" % host, data=json.dumps(es_query))
    if verbose:
        print("### sent: %s" % r.request.url, file=sys.stderr)
        print("### received status: %s" % r.status_code, file=sys.stderr)
    return r.json()['hits']['total']


range_desc = """
supports nagios-style ranges. The general format is “[@][start:][end]”. “start:” may be omitted if start==0.
“~:” means that start is negative infinity. If end is omitted, infinity is assumed.
To invert the match condition, prefix the range expression with “@”.
"""

o = argparse.ArgumentParser(description=__doc__)
o.add_argument('-m', '--query', help="the elasticsearch query to use", required=True)
o.add_argument('-H', '--host', help="name of the elasticsearch host", required=True)
o.add_argument('-w', '--warning', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-c', '--critical', metavar='RANGE', help=range_desc, required=True)
o.add_argument('-s', '--start', help="beginning of the time interval within which data is to be retrieved", default="now-1d")
o.add_argument('-e', '--end', help="end of the time interval within which data is to be retrieved", default="now")
o.add_argument('-V', '--version', action="version", version=__version__)
o.add_argument('-v', '--verbose', action="store_true", help="increase output verbosity")
options = o.parse_args()

# noinspection PyRedeclaration
verbose = options.verbose
nagiosplugin.Check(ElasticSearch(options.host, options.query, options.start, options.end),
                   nagiosplugin.ScalarContext("ElasticSearch", options.warning, options.critical)).main()