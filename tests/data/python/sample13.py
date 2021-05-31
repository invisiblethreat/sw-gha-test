import os
from utils.util_functions import full_exc_info, dictMerge
from utils.request_handlers import WebRequestHandler, log_close_webrequest_exception
from utils.version import *
from db_query_translator.epoch_filter import Filter
from db_query_translator.epoch_filter import generateExactMatchOrFilter, nestFilter, rewriteUserFilter
import ujson as json
from functools import partial
import subprocess
import copy
import collections
import sys, traceback
import itertools

from twisted.internet import reactor
import tornado.web
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest
from tornado import gen

from topology.v2.metric import Metric
from topology.v2.link import Link
from topology.v2.node import Node
from topology.v2.instance import Instance
from topology.v2.link_index import LinkIndex
from topology.v2.link_index import userNodeId, mergedNodeId, coarseGrainedMergedNodeId

from utils.constants import RESOURCES, DATASOURCES, SIGNATURE_PRIORITY_ORDER
from sets import Set

from topology.v2.node import USER_NODE_NAME, MERGED_NODE_NAME, constructInfraTagsFilterMap

# for profiling
import time

import re

import logging
import datadog

# Statsd instrumentation configuration
STOP_DOGSTATSD_INSTRUMENTATION = os.environ.get('STOP_DOGSTATSD_INSTRUMENTATION')
DO_STATSD_INSTRUMENTATION = STOP_DOGSTATSD_INSTRUMENTATION is None or (str(STOP_DOGSTATSD_INSTRUMENTATION).lower() != 'true')
STATSD_SERVER_ADDR = os.environ.get('STATSD_SERVER_ADDR')
STATSD_SERVER_ADDR_HOST = os.environ.get('HOST')
STATSD_SERVER_PORT = os.environ.get('STATSD_SERVER_PORT')
if STATSD_SERVER_ADDR is not None:
  statsdHost = STATSD_SERVER_ADDR
elif STATSD_SERVER_ADDR_HOST is not None:
  statsdHost = STATSD_SERVER_ADDR_HOST
else:
  statsdHost = '127.0.0.1'

if STATSD_SERVER_PORT is not None:
  statsdPort = int(STATSD_SERVER_PORT)
else:
  statsdPort = 8125
statsd = datadog.DogStatsd(host=statsdHost, port=statsdPort)

# Logging
log = logging.getLogger('Monitor.TopologyHandler')

IS_HA=str(os.environ.get('IS_HA', failobj='no'))
QUERY_TIMEOUT=int(os.environ.get('QUERY_TIMEOUT', failobj=10))

#ROUTING_INFO
TIME_SERIES_ENDPOINT_PORT = str(os.environ.get('TIME_SERIES_ENDPOINT_PORT', failobj=9047))
TIME_SERIES_ENDPOINT_HOST = str(os.environ.get('TIME_SERIES_ENDPOINT_HOST', failobj='127.0.0.1'))
DATASTORE = 'http://' + TIME_SERIES_ENDPOINT_HOST + ':' + TIME_SERIES_ENDPOINT_PORT

# Unclaimed signature uses a resource to populate
RESOURCE_DEQUE = collections.deque(["protocol", "uri", 'thrift', "mysql", "postgresql", "dns", "memcached", "redis", "cassandra", "dynamodb", "mongodb", "http2", "health", "infra"])

TOPOLOGY_DISPLAY_MAX_NODES = int(os.environ.get('TOPOLOGY_DISPLAY_MAX_NODES', failobj=250))
EXTERNAL_SERVICES_MAX_ITERATIONS=int(os.environ.get('EXTERNAL_SERVICES_MAX_ITERATIONS', failobj=200))

aggregateToAggType = {
  "METRIC_0": "count",
  "METRIC_1": "sum",
  "METRIC_2": "throughput",
  "METRIC_3": "kbps",
  "METRIC_4": "cardinality"
}

metricTypeToAggregate = {
  "count": "METRIC_0",
  "sum": "METRIC_1",
  "throughput": "METRIC_2",
  "traffic_rate": "METRIC_3",
  "cardinality": "METRIC_4"
}

queryMetrics = {
  "protocol":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    },
    "METRIC_3":{
      "aggregate": aggregateToAggType["METRIC_3"]
    }
  },
  "uri":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "thrift":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "mysql":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "postgresql":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "dns":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "memcached":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "redis":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "cassandra":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "dynamodb":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "mongodb":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "http2":{
    "METRIC_0":{
      "aggregate": aggregateToAggType["METRIC_0"]
    },
    "METRIC_1":{
      "aggregate": aggregateToAggType["METRIC_1"]
    },
    "METRIC_2":{
      "aggregate": aggregateToAggType["METRIC_2"]
    }
  },
  "infra": {
    "METRIC_4": {
      "aggregate": "cardinality",
      "columns": ["instance.id"]
    }
  }
}

metadatas = {
  "protocol":{
    "count": {"name": "TCP Connections", "unit": "transactions", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "tps", "marquee": True},
    "traffic_rate": {"name": "Traffic Rate", "unit": "kBps", "marquee": True}
  },
  "uri":{
    "count": {"name": "Total Calls", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "thrift":{
    "count": {"name": "Total Calls", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "mysql":{
    "count": {"name": "Total Queries", "unit": "queries", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "qps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "postgresql":{
    "count": {"name": "Total Queries", "unit": "queries", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "qps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "dns":{
    "count": {"name": "Total Lookups", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "memcached":{
    "count": {"name": "Total Commands", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "redis":{
    "count": {"name": "Total Commands", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "cassandra":{
    "count": {"name": "Total Queries", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "dynamodb":{
    "count": {"name": "Total Queries", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "mongodb":{
    "count": {"name": "Total Commands", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "http2":{
    "count": {"name": "Total Calls", "unit": "requests", "marquee": False},
    "throughput": {"name": "Throughput", "unit": "rps", "marquee": True},
    "latency": {"name": "Latency", "unit": "ms", "marquee": True}
  },
  "infra": {
    "cardinality": {"name": "Cardinality", "unit": "instances", "marquee": False}
  }
}

names = {
  "protocol": "Protocols",
  "uri": "Uri",
  "thrift": "Thrift",
  "mysql": "MySQL",
  "postgresql": "PostgreSQL",
  "dns": "Dns",
  "memcached": "Memcached",
  "redis": "Redis",
  "cassandra": "Cassandra",
  "dynamodb": "DynamoDB",
  "mongodb": "MongoDB",
  "http2": "Http2",
  "infra": "Infra"
}

# need to set GRAPH_QUERY["options"]["Metrics"] and GRAPH_QUERY["options"]["GroupBy"]["SERIES_4"]
EXTERNAL_SERVICES_GRAPH_QUERY = {
  "options":{
    "Metrics":{},
    "GroupBy": {
      "SERIES_0": "server.id"
    }
  }
}

# need to set EVENTS_QUERY["queries"]["options"]["INTERVALS"]
EVENTS_QUERY = {
  "queries":{
    "report-name":"events.alert.open",
    "options":{
      "GroupBy":{
        "SERIES_0": "trigger_id",
        "SERIES_1": "group_info",
        "SERIES_2": "alert_config",
        "SERIES_3": "severity"
      },
      "Metrics": {
        "METRIC_0":{
          "aggregate":"sum",
          "column":""
        }
      },
      "FILTER": {
        "type": "or",
        "fields": [
          {
            "column": "severity",
            "type": "match",
            "value": {
              "text": "critical"
            }
          },
          {
            "column": "severity",
            "type": "match",
            "value": {
              "text": "warning"
            }
          },
          {
            "column": "severity",
            "type": "match",
            "value": {
              "text": "unknown"
            }
          }
        ]
      }
    }
  }
}

# health levels for a service
NORMAL    = 0
WARNING   = 1
CRITICAL  = 2
UNKNOWN   = 3

SEVERITY_HEALTH_MAP = {
  'normal': 0,
  'warning': 1,
  'critical': 2,
  'unknown': 3
}

def generateExternalServicesGraphQuery(resourceType):
  retVal = copy.deepcopy(EXTERNAL_SERVICES_GRAPH_QUERY)
  metrics = queryMetrics[resourceType]
  retVal["options"]["Metrics"] = metrics
  if resourceType in RESOURCES:
    resource = RESOURCES[resourceType]
    retVal["options"]["GroupBy"]["SERIES_1"] = resource
  return retVal

# need to set GRAPH_OTHER_QUERY["options"]["Metrics"]
EXTERNAL_SERVICES_GRAPH_OTHER_QUERY = {
  "options":{
    "Metrics":{},
    "GroupBy": {
      "SERIES_0": "server.id"
    }
  }
}
def generateExternalServicesGraphOtherQuery(resourceType):
  retVal = copy.deepcopy(EXTERNAL_SERVICES_GRAPH_OTHER_QUERY)
  metrics = queryMetrics[resourceType]
  retVal["options"]["Metrics"] = metrics
  return retVal

# need to set TOPK_QUERY["options"]["GroupBy"]["SERIES_0"]
TOPK_QUERY = {
  "options":{
    "Metrics":{
      "METRIC_0":{
        "aggregate": "count"
      }
    },
    "GroupBy":
    {"SERIES_0": ""}
  }
}
def externalServicesGenerateTopKQuery(resourceType):
  retVal = copy.deepcopy(TOPK_QUERY)
  resource = RESOURCES[resourceType]
  retVal["options"]["GroupBy"]["SERIES_0"] = resource
  return retVal

COVER_INSTANCES_QUERY = {
  "options":{
    "Metrics":{
      "METRIC_0":{
        "aggregate": "count"
      }
    },
    "GroupBy":
    {"SERIES_0": "server.id"}
  }
}

def addNewFilter(query, newFilter):
  # check if there's an existing filter
  if "FILTER" in query["options"]:
    existingFilterDict = query["options"]["FILTER"]
    existingFilter = Filter.deserialize(existingFilterDict)
    combinedFilter = Filter("and")
    combinedFilter.appendField(existingFilter)
    combinedFilter.appendField(newFilter)
    query["options"]["FILTER"] = combinedFilter.serialize()
  else:
    query["options"]["FILTER"] = newFilter.serialize()


DYNAMIC_GRAPH_QUERY = {
  "options":{
    "Metrics":{},
    "GroupBy": {}
  }
}

CARDINALITY_QUERY ={
    "options":{
      "Metrics": {},
      "GroupBy": {}
    }
}

def generateCardinalityQuery(instanceType, queryOptions, groupbys, userFilterForInstanceType):
  retVal = copy.deepcopy(CARDINALITY_QUERY)
  groupByDict = TopologyServicesHandlerV2.getGroupBy(groupbys, instanceType)

  # to get each instance type counts
  groupByDict["instance.instance_type"] = "instance.instance_type"

  retVal["options"]["GroupBy"] = groupByDict
  if userFilterForInstanceType:
    retVal["options"]["FILTER"] = userFilterForInstanceType

  if queryOptions != {}:
    retVal["options"] = dictMerge(queryOptions, retVal["options"])

  allValuesFilter = {
    "type": "all_values",
    "column": "instance",
    "value": {
      "text": ""
    }
  }
  nestFilter(retVal, allValuesFilter)

  # get rid of the topk clause from the query
  if "LIMIT" in retVal["options"]:
    del retVal["options"]["LIMIT"]

  return retVal

'''
Topology Handler
'''
class TopologyServicesHandlerV2(WebRequestHandler):
  @tornado.web.asynchronous
  def post(self):
    json_obj = json.loads(self.request.body)
    if "options" in json_obj:
      self.queryOptions = json_obj["options"]
    else:
      self.queryOptions = {}
    self.triggerIds = []
    self.triggeredGroupsToEvent = {}
    self.triggeredGroupsHealthMap = {}
    self.userFilter = {}
    self.access_token = self.request.headers.get('x-access-token', '')
    self.organization_id = self.request.headers.get('x-organization-id', '')
    if IS_HA == 'yes' and not self.organization_id:
      log.warn('Organization ID not found in the request header')
    self.entryStage()

  def profileStage(self, name, resource="global"):
    if DO_STATSD_INSTRUMENTATION:
      now = time.time()
      duration = now - self.lastTime[resource]
      statsd.gauge('topology_stage_duration', duration, tags=['resource:' + resource, 'stage:' + name])
      self.lastTime[resource] = now

  def entryStage(self):
    log.debug("entryStage")
    # time the stages
    if DO_STATSD_INSTRUMENTATION:
      lastTime = time.time()
      self.lastTime = {"global": lastTime}
      for resource in RESOURCE_DEQUE:
        self.lastTime[resource] = lastTime
    # linkIndex
    self.linkIndex = LinkIndex()

    # fix the query end time
    now = int(time.time() * 1000)
    '''
    5 second slack to allow for in-flux stats at realtime ingestion -- this is a
    conservative estimate as the exact slack is determined by the time series backend
    '''
    effectiveNow = now - 5000
    intervalFields = self.queryOptions.get("INTERVALS", [])
    for intervalField in intervalFields:
      if len(intervalField) == 1:
        intervalField.append(effectiveNow)

    self.aborted=False
    self.stat_counter = 0

    ''' topk trackers '''
    # topKResources -- {<resourceType>: <set of top resources>}
    self.topKResources = dict((resourceType,set()) for resourceType in RESOURCE_DEQUE)
    # allInstances -- {<resourceType>: <set of instance ids>}
    self.allInstances = dict((resourceType,set()) for resourceType in RESOURCE_DEQUE)
    # coveredInstances -- {<resourceType>: <set of instance ids>}
    self.coveredInstances = dict((resourceType,set()) for resourceType in RESOURCE_DEQUE)
    # iterations -- {<resourceType>: <num iterations>}
    self.iterations = dict((resourceType,0) for resourceType in RESOURCE_DEQUE)

    ''' clustering trackers '''
    # inResources -- {<resourceType>: {<resource>: <nodeId>}}
    self.inResources = dict((resourceType,{}) for resourceType in RESOURCE_DEQUE)
    # outResourceSets -- {<resourceType>: {<resource>: <nodeId>}}
    self.outResources = dict((resourceType,{}) for resourceType in RESOURCE_DEQUE)
    # outResourceSets -- {<resourceType>: {<resource>: <nodeId>}}
    # coarseGrainedNodes - <resourceKey: nodeId>
    self.coarseGrainedNodes = {}

    # userNode -- <node>
    self.userNode = Node(Instance({"id": userNodeId, "instance_type": "user", "entry_node": "entry_node"}, userNodeId), "user_node", Metric({}), Metric({}), Metric({}), USER_NODE_NAME)
    # mergedNode -- <node>
    self.mergedNode = Node(Instance({"id": mergedNodeId, "instance_type": "merged", "merged_node": "merged_node"}, mergedNodeId), "merged_node", Metric({}), Metric({}), Metric({}), MERGED_NODE_NAME)

    self.nodes = {}

    # resourceProgressCounter -- <counter>
    self.resourceProgressCounter = 0

    self.topologyFilter = {}
    self.infraTopologyFilter = {}

    # parse top k
    self.topk = -1
    self.topkMetric = "count"
    if "LIMIT" in self.queryOptions:
      if "value" in self.queryOptions["LIMIT"]:
        self.topk = self.queryOptions["LIMIT"]["value"]
      if "column" in self.queryOptions["LIMIT"]:
        self.topkMetric = self.queryOptions["LIMIT"]["column"]
    if self.topk > 0:
      self.topkFlag = True
    else:
      self.topkFlag = False

    self.resourceDeque = copy.deepcopy(RESOURCE_DEQUE)

    # get rid of FILTER clause from options
    if "FILTER" in self.queryOptions:
      self.userFilter = copy.deepcopy(self.queryOptions["FILTER"])
      del self.queryOptions["FILTER"]

    self.tagsByResourceKey = {}

    self.remainingNodesBehavior = self.queryOptions.get("remaining", "auto")

    self.mergedResources = {}

    # server.instance_type equals remote and not filter
    self.serverRemoteFilter = {
      "type":"match",
      "column":"server.instance_type",
      "value":{
        "text":"remote"
      }
    }
    self.serverNotRemoteFilter = {
      "type": "not",
      "field": [self.serverRemoteFilter]
    }

    # client.instance_type equals remote and not filter
    self.clientRemoteFilter = {
      "type":"match",
      "column":"client.instance_type",
      "value":{
        "text":"remote"
      }
    }
    self.clientNotRemoteFilter = {
      "type": "not",
      "field": [self.clientRemoteFilter]
    }

    # instance.instance_type equals remote and not filter
    self.instanceRemoteFilter = {
      "type":"match",
      "column":"instance.instance_type",
      "value":{
        "text":"remote"
      }
    }
    self.instanceNotRemoteFilter = {
      "type": "not",
      "field": [self.instanceRemoteFilter]
    }

    # construct server user filter
    serverUserFilter = copy.deepcopy(self.userFilter)
    rewriteUserFilter(serverUserFilter, "server")
    self.serverUserFilter = None
    self.serverNotUserFilter = None

    # construct server user filter
    clientUserFilter = copy.deepcopy(self.userFilter)
    rewriteUserFilter(clientUserFilter, "client")
    self.clientUserFilter = None
    self.clientNotUserFilter = None

    # construct instance user filter
    instanceUserFilter=copy.deepcopy(self.userFilter)
    rewriteUserFilter(instanceUserFilter, "instance")
    self.instanceUserFilter = None
    self.instanceNotUserFilter = None

    # server user filter and not filter
    if serverUserFilter:
      self.serverUserFilter = serverUserFilter
      self.serverNotUserFilter = {
        "type": "not",
        "field": [self.serverUserFilter]
      }

    # client user filter and not filter
    if clientUserFilter:
      self.clientUserFilter = clientUserFilter
      self.clientNotUserFilter = {
        "type": "not",
        "field": [self.clientUserFilter]
      }

    # instance user filter and not filter
    if instanceUserFilter:
      self.instanceUserFilter = instanceUserFilter
      self.instanceNotUserFilter = {
        "type": "not",
        "field": [self.instanceUserFilter]
      }

    self.groupByAndFilterTags = set()
    self.groupByTags = set()
    self.filterTags = set()

    topologyGroupBy = self.queryOptions.get("groupby", {})
    for tGroup in topologyGroupBy:
      self.groupByAndFilterTags.add(tGroup)
      self.groupByTags.add(tGroup)

    filterGroupBy = constructInfraTagsFilterMap(self.instanceUserFilter).keys()
    for fGroup in filterGroupBy:
      self.groupByAndFilterTags.add(fGroup)
      self.filterTags.add(fGroup)

    self.metadataStageUniqueNodes = set()

    self.resourceComponent()

  def resourceComponent(self):
    log.debug("resourceComponent")
    for resourceType in self.resourceDeque:
      log.debug("resourceType: " + resourceType)
      self.metadataStage(resourceType)

  ''' Topology Processing Pipeline Begins '''
  ### Metadata Stage Begins ###
  def metadataStage(self, resourceType):
    if resourceType == "health":
      requestBody = copy.deepcopy(EVENTS_QUERY)
      requestBody["queries"]["options"]["INTERVALS"] = self.queryOptions.get("INTERVALS", [])
      requestData(self, DATASOURCES["health"], requestBody, partial(self.handleTriggerIdResponse), partial(self.finishTriggerIdResponse))
    else:
      if resourceType == "infra":
        stageInstanceFilter = {
          "type": "and",
          "fields": []
        }
        if self.instanceNotRemoteFilter:
          stageInstanceFilter["fields"].append(self.instanceNotRemoteFilter)
        if self.instanceUserFilter:
          stageInstanceFilter["fields"].append(self.instanceUserFilter)
        stageQuery = generateCardinalityQuery("instance", self.queryOptions, self.groupByTags, stageInstanceFilter)
        stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
        requestBody = {
          "queries": stageQuery
        }
        requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleCardinality, resourceType), partial(self.finishCardinality, resourceType))
      else:
        if not self.groupByAndFilterTags and self.remainingNodesBehavior == "auto":
          # if we don't have group by tags and we need to show external nodes, call dynamicGraphIn directly
          self.dynamicGraphInStage(resourceType)
        else:
          # call dynamic graph for other resource types like uri, protocol, mysql etc.
          self.dynamicGraphStage(resourceType)

  def handleCardinality(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    if not serverInstance:
      log.error('Unexpected state: serverInstance cannot be null')
      return

    serverMetadataJson = safeJsonLoads(serverMetadata)
    instanceType = serverMetadataJson.get("instance_type", None)
    if not instanceType:
      log.warn("Unexpected State: instance_type can't be None or empty")
      return

    if instanceType not in ["host", "pod", "container"]:
      log.warn("Unexpected instance_type: " + str(instance_type))
      return

    # remove synthetic instance_type
    if not 'instance_type' in self.groupByTags:
      del serverMetadataJson['instance_type']

    # if user didn't specify an instance_type and group by tag was empty, we need a synthetic coarse grained node
    if not self.groupByTags:
      serverInstance = coarseGrainedMergedNodeId
      serverMetadata = ""

    globalMetrics = {
      "global": copy.deepcopy(metricsDict),
      "other": copy.deepcopy(metricsDict)
    }

    metadatas[resourceType]["cardinality"]["unit"] = str(instanceType) + "s"
    infraMetric = Metric({
      instanceType: {
        "resource_metrics": {},
        "global_metrics": globalMetrics,
        "dominant": None,
        "metadata": metadatas[resourceType],
        "name": names[resourceType]
      }
    })
    serverMetadataJsonStr = json.dumps(serverMetadataJson)
    self.metadataStageUniqueNodes.add(serverMetadataJsonStr)
    self.findOrCreateInstance(serverInstance, serverMetadataJsonStr, nodeType="coarse_grained", infraMetric=infraMetric)

  def finishCardinality(self, resourceType, response):
    self.profileStage("cardinality", resourceType)
    if resourceType == "infra":
      if len(self.metadataStageUniqueNodes) > TOPOLOGY_DISPLAY_MAX_NODES: # return immediately if we reached max nodes we can display
        error_str = "Topology too large, add filters or use less granular groupbys"
        self.returnTopologyResponse(None, None, error=RuntimeError(error_str))
      else:
        self.commitResourceCompletion()
    else:
      log.error('Unexpected resourceType: ' + str(resourceType))
  ### Metadata Stage Ends ###


  ### Dynamic Graph Stages Begin ###
  @staticmethod
  def getGroupBy(groupBys, columnPrefix):
    groupByDict = {}
    for group in groupBys:
        key = columnPrefix + '.' + group # g['server.id'] = 'server.id'
        groupByDict[key] = key
    return groupByDict

  @staticmethod
  def getStageMetric(resourceType, metricsDict):
      if resourceType == "infra":
        return

      globalMetrics = {
        "global": copy.deepcopy(metricsDict),
        "other": copy.deepcopy(metricsDict)
      }
      metric = Metric({
        resourceType: {
          "resource_metrics": {},
          "global_metrics": globalMetrics,
          "dominant": None,
          "metadata": metadatas[resourceType],
          "name": names[resourceType]
        }
      })
      return metric

  def dynamicGraphStage(self, resourceType):
    if resourceType != "infra":

        # if there is no groupby don't proceed
        if not self.groupByAndFilterTags:
          self.commitResourceCompletion()
          return

        stageQuery = copy.deepcopy(DYNAMIC_GRAPH_QUERY)
        serverGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "server")
        clientGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "client")
        groupByDict = dictMerge(serverGroupByDict, clientGroupByDict)
        stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
        stageQuery["options"]["GroupBy"] = groupByDict

        if self.queryOptions != {}:
          stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

        # get rid of the topk clause from the query
        if "LIMIT" in stageQuery["options"]:
          del stageQuery["options"]["LIMIT"]

        stageServerFilter = {
          "type": "and",
          "fields": []
        }
        if self.serverNotRemoteFilter:
          stageServerFilter["fields"].append(self.serverNotRemoteFilter)
        if self.serverUserFilter:
          stageServerFilter["fields"].append(self.serverUserFilter)

        stageClientFilter = {
          "type": "and",
          "fields": []
        }
        if self.clientNotRemoteFilter:
          stageClientFilter["fields"].append(self.clientNotRemoteFilter)
        if self.clientUserFilter:
          stageClientFilter["fields"].append(self.clientUserFilter)

        stageInstanceFilter = {
          "type": "and",
          "fields": []
        }
        if self.instanceNotRemoteFilter:
          stageInstanceFilter["fields"].append(self.instanceNotRemoteFilter)
        if self.instanceUserFilter:
          stageInstanceFilter["fields"].append(self.instanceUserFilter)

        if resourceType == "infra":
          stageFilter = stageInstanceFilter
        else:
          stageFilter = {
            "type": "and",
            "fields": [
              stageServerFilter,
              stageClientFilter
            ]
          }

        nestFilter(stageQuery, stageFilter)

        requestBody = {
          "queries": stageQuery,
        }

        requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleDynamicGraphStage, resourceType), partial(self.finishDynamicGraphStage, resourceType))
    else:
        log.error("Unexpected state: Resource type can't be Infra")

  def handleDynamicGraphStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
      metric = self.getStageMetric(resourceType, metricsDict)
      if clientInstance != None and serverInstance != None:
          self.findOrCreateInstance(clientInstance, clientMetadata, nodeType="coarse_grained", outMetric=metric)
          self.findOrCreateInstance(serverInstance, serverMetadata, nodeType="coarse_grained", inMetric=metric)
          self.linkInstances(clientInstance, serverInstance, metric)
      else:
          # don't proceed
          log.error('Unexpected state: serverInstance or Client Instance cannot be null')
          return

  def finishDynamicGraphStage(self, resourceType, response):
    self.dynamicGraphInStage(resourceType)

  def dynamicGraphInStage(self, resourceType):
      serverGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "server")
      groupByDict = serverGroupByDict

      stageQuery = copy.deepcopy(DYNAMIC_GRAPH_QUERY)
      stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
      stageQuery["options"]["GroupBy"] = groupByDict

      if self.queryOptions != {}:
        stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

      # get rid of the topk clause from the query
      if "LIMIT" in stageQuery["options"]:
        del stageQuery["options"]["LIMIT"]

      stageServerFilter = {
        "type": "and",
        "fields": []
      }
      if self.serverNotRemoteFilter:
        stageServerFilter["fields"].append(self.serverNotRemoteFilter)
      if self.serverUserFilter:
        stageServerFilter["fields"].append(self.serverUserFilter)

      stageClientFilter = {
        "type": "and",
        "fields": []
      }
      if self.clientRemoteFilter:
        stageClientFilter["fields"].append(self.clientRemoteFilter)

      stageInstanceFilter = {
        "type": "and",
        "fields": []
      }
      if self.instanceNotRemoteFilter:
        stageInstanceFilter["fields"].append(self.instanceNotRemoteFilter)
      if self.instanceUserFilter:
        stageInstanceFilter["fields"].append(self.instanceUserFilter)

      if resourceType == "infra":
        stageFilter = stageInstanceFilter
      else:
        stageFilter = {
          "type": "and",
          "fields": [
            stageServerFilter,
            stageClientFilter
          ]
        }

      nestFilter(stageQuery, stageFilter)

      requestBody = {
        "queries": stageQuery,
      }

      requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleDynamicGraphInStage, resourceType), partial(self.finishDynamicGraphInStage, resourceType))

  def handleDynamicGraphInStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    # get metric
    metric = self.getStageMetric(resourceType, metricsDict)

    # create/update coarse grained server instances
    if serverInstance == None:
      if not self.groupByAndFilterTags:
        serverInstance = coarseGrainedMergedNodeId
        serverMetadata = ""
        self.findOrCreateInstance(serverInstance, serverMetadata, nodeType="coarse_grained", inMetric=metric)
      else:
        log.error('Unexpected State: serverInstance cannot be None')
        return
    else:
      self.findOrCreateInstance(serverInstance, serverMetadata, nodeType="coarse_grained", inMetric=metric)

    # create entry (client) node and link to server instances only if group by RemoteAPI is specified
    if self.remainingNodesBehavior == "auto":
      clientInstance = json.dumps(self.userNode.instance.instanceId)
      clientMetadata = json.dumps(self.userNode.instance.metadata)
      self.findOrCreateInstance(clientInstance, clientMetadata, nodeType="user_node", outMetric=metric)
      self.linkInstances(clientInstance, serverInstance, metric)

  def finishDynamicGraphInStage(self, resourceType, response):
      self.dynamicGraphOutStage(resourceType)

  def dynamicGraphOutStage(self, resourceType):
    clientGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "client")
    groupByDict = clientGroupByDict

    # add server.id to group by only if groupby RemoteAPI
    if self.remainingNodesBehavior == "auto":
      groupByDict["server.id"] = "server.id"

    stageQuery = copy.deepcopy(DYNAMIC_GRAPH_QUERY)
    stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
    stageQuery["options"]["GroupBy"] = groupByDict
    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # get rid of the topk clause from the query
    if "LIMIT" in stageQuery["options"]:
      del stageQuery["options"]["LIMIT"]

    stageServerFilter = {
      "type": "and",
      "fields": []
    }
    if self.serverRemoteFilter:
      stageServerFilter["fields"].append(self.serverRemoteFilter)

    stageClientFilter = {
      "type": "and",
      "fields": []
    }
    if self.clientNotRemoteFilter:
      stageClientFilter["fields"].append(self.clientNotRemoteFilter)
    if self.clientUserFilter:
      stageClientFilter["fields"].append(self.clientUserFilter)

    stageInstanceFilter = {
      "type": "and",
      "fields": []
    }
    if self.instanceRemoteFilter:
      stageInstanceFilter["fields"].append(self.instanceRemoteFilter)

    if resourceType == "infra":
      stageFilter = stageInstanceFilter
    else:
      stageFilter = {
        "type": "and",
        "fields": [
          stageServerFilter,
          stageClientFilter
        ]
      }

    nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleDynamicGraphOutStage, resourceType), partial(self.finishDynamicGraphOutStage, resourceType))

  def handleDynamicGraphOutStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    # get metric
    metric = self.getStageMetric(resourceType, metricsDict)

    # create/update coarse grained client instances
    if clientInstance == None:
      if not self.groupByAndFilterTags:
        clientInstance = coarseGrainedMergedNodeId
        clientMetadata = ""
        self.findOrCreateInstance(clientInstance, clientMetadata, nodeType="coarse_grained", outMetric=metric)
      else:
        log.error('Unexpected State: clientInstance cannot be None')
        return
    else:
      self.findOrCreateInstance(clientInstance, clientMetadata, nodeType="coarse_grained", outMetric=metric)

    # create remote server nodes and link to client instances only if group by RemoteAPI is specified
    if self.remainingNodesBehavior == "auto":
      if serverInstance == None:
        log.error('Unexpected State: serverInstance cannot be None')
        return
      self.allInstances[resourceType].add(serverInstance)
      self.findOrCreateInstance(serverInstance, serverMetadata, nodeType="fine_grained", inMetric=metric)
      self.linkInstances(clientInstance, serverInstance, metric)

  def finishDynamicGraphOutStage(self, resourceType, response):
    # absence of server/client user filter means that we don't need to update coarse node stats
    if not self.serverUserFilter or not self.clientUserFilter:
      # call auto grouping algorithm only if groupby RemoteAPI is specified
      if self.remainingNodesBehavior == "auto":
        self.externalServicesGraphStage(resourceType)
      else:
        self.commitResourceCompletion()
    else: # update coarse node with stats for filtered out servers and clients
      self.updateCoarseServerStatsStage(resourceType)

  def updateCoarseServerStatsStage(self, resourceType):
    serverGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "server")
    groupByDict = serverGroupByDict

    stageQuery = copy.deepcopy(DYNAMIC_GRAPH_QUERY)
    stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
    stageQuery["options"]["GroupBy"] = groupByDict
    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # get rid of the topk clause from the query
    if "LIMIT" in stageQuery["options"]:
      del stageQuery["options"]["LIMIT"]

    stageServerFilter = {
      "type": "and",
      "fields": []
    }
    if self.serverUserFilter:
      stageServerFilter["fields"].append(self.serverUserFilter)

    stageClientFilter = {
      "type": "and",
      "fields": []
    }
    if self.clientNotRemoteFilter:
      stageClientFilter["fields"].append(self.clientNotRemoteFilter)
    if self.clientNotUserFilter:
      stageClientFilter["fields"].append(self.clientNotUserFilter)

    stageFilter = {
      "type": "and",
      "fields": []
    }
    if stageClientFilter["fields"]:
      stageFilter["fields"].append(stageClientFilter)
    if stageServerFilter["fields"]:
      stageFilter["fields"].append(stageServerFilter)

    nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleUpdateCoarseServerStatsStage, resourceType), partial(self.finishUpdateCoarseServerStatsStage, resourceType))

  def handleUpdateCoarseServerStatsStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    metric = self.getStageMetric(resourceType, metricsDict)
    self.findOrCreateInstance(serverInstance, serverMetadata, nodeType="coarse_grained", inMetric=metric)

  def finishUpdateCoarseServerStatsStage(self, resourceType, response):
    self.updateCoarseClientStatsStage(resourceType)

  def updateCoarseClientStatsStage(self, resourceType):
    clientGroupByDict = self.getGroupBy(self.groupByAndFilterTags, "client")
    groupByDict = clientGroupByDict

    stageQuery = copy.deepcopy(DYNAMIC_GRAPH_QUERY)
    stageQuery["options"]["Metrics"] = queryMetrics[resourceType]
    stageQuery["options"]["GroupBy"] = groupByDict
    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # get rid of the topk clause from the query
    if "LIMIT" in stageQuery["options"]:
      del stageQuery["options"]["LIMIT"]

    stageServerFilter = {
      "type": "and",
      "fields": []
    }
    if self.serverNotRemoteFilter:
      stageServerFilter["fields"].append(self.serverNotRemoteFilter)
    if self.serverNotUserFilter:
      stageServerFilter["fields"].append(self.serverNotUserFilter)

    stageClientFilter = {
      "type": "and",
      "fields": []
    }
    if self.clientUserFilter:
      stageClientFilter["fields"].append(self.clientUserFilter)

    stageFilter = {
      "type": "and",
      "fields": []
    }
    if stageClientFilter["fields"]:
      stageFilter["fields"].append(stageClientFilter)
    if stageServerFilter["fields"]:
      stageFilter["fields"].append(stageServerFilter)

    nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleUpdateCoarseClientStatsStage, resourceType), partial(self.finishUpdateCoarseClientStatsStage, resourceType))

  def handleUpdateCoarseClientStatsStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    metric = self.getStageMetric(resourceType, metricsDict)
    self.findOrCreateInstance(clientInstance, clientMetadata, nodeType="coarse_grained", outMetric=metric)

  def finishUpdateCoarseClientStatsStage(self, resourceType, response):
    # call auto grouping algorithm only if we have groupby RemoteAPI
    if self.remainingNodesBehavior == "auto":
      self.externalServicesGraphStage(resourceType)
    else:
      self.commitResourceCompletion()
  ### Dynamic Graph Stages End ###


  ### External Services Graph Stage Begins ###
  def getExternalServiceStageFilter(self):
    # server.instance_type == remote
    stageServerFilter = self.serverRemoteFilter

    # client.instance_type != remote && FU_c
    stageClientFilter = {
      "type": "and",
      "fields": []
    }
    if self.clientNotRemoteFilter:
      stageClientFilter["fields"].append(self.clientNotRemoteFilter)
    if self.clientUserFilter:
      stageClientFilter["fields"].append(self.clientUserFilter)

    stageFilter = {
      "type": "and",
      "fields": [
        stageServerFilter,
        stageClientFilter
      ]
    }
    return stageFilter

  def externalServicesGraphStage(self, resourceType):
    topkFlag = self.topkFlag
    if resourceType in ['memcached', 'redis']:
      # for resourceType's that do not have fine-grained resources
      topkFlag = False
    if topkFlag:
      self.externalServicesTopKComponent(resourceType)
    else:
      stageQuery = generateExternalServicesGraphQuery(resourceType)
      if self.queryOptions != {}:
        stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

      if "LIMIT" in stageQuery["options"]:
        del stageQuery["options"]["LIMIT"]

      stageFilter = self.getExternalServiceStageFilter()
      if stageFilter:
        nestFilter(stageQuery, stageFilter)

      requestBody = {
        "queries": stageQuery,
      }

      requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleExternalServicesGraphStage, resourceType), partial(self.finishExternalServicesGraphStage, resourceType))

  def externalServicesTopKComponent(self, resourceType):
    log.debug("topKComponent")
    self.iterations[resourceType] = self.iterations[resourceType] + 1
    # robustness: if more than 100 iterations break!
    log.debug("num iterations: " + str(self.iterations[resourceType]))
    if self.iterations[resourceType] > EXTERNAL_SERVICES_MAX_ITERATIONS:
      log.warn("activate fail safe: more than " + str(EXTERNAL_SERVICES_MAX_ITERATIONS) + " iterations reached for resourceType: " + str(resourceType))
      self.externalServicesGraphTopKStage(resourceType)
      # terminate
      return
    if len(self.coveredInstances[resourceType]) == len(self.allInstances[resourceType]):
      # break condition
      log.debug("break topk")
      log.info("External Services TopK Stage for resource " + str(resourceType) + " converged after " + str(self.iterations[resourceType]) + " iterations")
      self.externalServicesGraphTopKStage(resourceType)
    else:
      log.debug("continue topk, covered instances: " + str(len(self.coveredInstances[resourceType])) + " all instances: " + str(len(self.allInstances[resourceType])))
      self.externalServicesTopKStage(resourceType)

  def externalServicesTopKStage(self, resourceType):
    log.debug("topKStage")
    # compute the set of top resources
    stageQuery = externalServicesGenerateTopKQuery(resourceType)

    # add negative coveredInstances filter
    if len(self.coveredInstances[resourceType]) > 0:
      stageFilter = generateExactMatchOrFilter("server.id", self.coveredInstances[resourceType])
      temp = stageFilter
      stageFilter = Filter("not", None, None, None, [temp])
      addNewFilter(stageQuery, stageFilter)

    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    stageFilter = self.getExternalServiceStageFilter()
    if stageFilter:
      nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleExternalServicesTopK, resourceType), partial(self.finishExternalServicesTopK, resourceType))

  def handleExternalServicesTopK(self, resourceType, seriesDict, metricsDict):
    resourceVal = seriesDict[resourceType]
    if resourceVal == None:
      log.warn("query returned incomplete result row, resourceType: " + str(resourceType) + ", seriesDict: " + str(seriesDict) + ", metricsDict: " + str(metricsDict))
      return

    # poplulate the set of top resources
    self.topKResources[resourceType].add(resourceVal)

  def finishExternalServicesTopK(self, resourceType, response):
    self.profileStage("topk", resourceType)
    self.coverInstancesStage(resourceType)

  def coverInstancesStage(self, resourceType):
    log.debug("coverInstancesStage")
    # compute the set of covered instances
    stageQuery = copy.deepcopy(COVER_INSTANCES_QUERY)
    # add topKResources filter
    if len(self.topKResources[resourceType]) > 0:
      stageFilter = generateExactMatchOrFilter(RESOURCES[resourceType], self.topKResources[resourceType])
      addNewFilter(stageQuery, stageFilter)

    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # get rid of the topk clause from the query
    del stageQuery["options"]["LIMIT"]

    stageFilter = self.getExternalServiceStageFilter()
    if stageFilter:
      nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleCoverInstances, resourceType), partial(self.finishCoverInstances, resourceType))

  def handleCoverInstances(self, resourceType, seriesDict, metricsDict, serverInstance=None):
    # poplulate the set of covered instances
    self.coveredInstances[resourceType].add(serverInstance)
    # robustness: any instance that wasn't in all but seen during covering should be added to all set
    if serverInstance not in self.allInstances[resourceType]:
      self.allInstances[resourceType].add(serverInstance)

  def finishCoverInstances(self, resourceType, response):
    self.profileStage("cover instances", resourceType)
    self.externalServicesTopKComponent(resourceType)

  def externalServicesGraphTopKStage(self, resourceType):
    log.debug("graphTopKStage")
    # graph just the topk resources
    stageQuery = generateExternalServicesGraphQuery(resourceType)
    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # add the filter for topk resources
    if len(self.topKResources[resourceType]) > 0:
      stageFilter = generateExactMatchOrFilter(RESOURCES[resourceType], self.topKResources[resourceType])
      addNewFilter(stageQuery, stageFilter)

    # get rid of the topk clause from the query
    del stageQuery["options"]["LIMIT"]

    stageFilter = self.getExternalServiceStageFilter()
    if stageFilter:
      nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleExternalServicesGraphStage, resourceType), partial(self.finishExternalServicesTopKGraph, resourceType))

  def finishExternalServicesTopKGraph(self, resourceType, response):
    self.profileStage("graph topk", resourceType)
    log.debug("link index: " + str(self.linkIndex.index) + ", link reverse index: " + str(self.linkIndex.reverseIndex))
    self.externalServicesGraphOtherStage(resourceType)

  def externalServicesGraphOtherStage(self, resourceType):
    log.debug("graphOtherStage")
    # graph other than topk resources
    stageQuery = generateExternalServicesGraphOtherQuery(resourceType)
    if self.queryOptions != {}:
      stageQuery["options"] = dictMerge(self.queryOptions, stageQuery["options"])

    # add the filter for other than topk resources
    if len(self.topKResources[resourceType]) > 0:
      stageFilter = generateExactMatchOrFilter(RESOURCES[resourceType], self.topKResources[resourceType])
      temp = stageFilter
      stageFilter = Filter("not", None, None, None, [temp])
      addNewFilter(stageQuery, stageFilter)

    # get rid of the topk clause from the query
    del stageQuery["options"]["LIMIT"]

    stageFilter = self.getExternalServiceStageFilter()
    if stageFilter:
      nestFilter(stageQuery, stageFilter)

    requestBody = {
      "queries": stageQuery,
    }

    requestData(self, DATASOURCES[resourceType], requestBody, partial(self.handleExternalServicesGraphStage, resourceType), partial(self.finishExternalServicesGraphStage, resourceType))

  def handleExternalServicesGraphStage(self, resourceType, seriesDict, metricsDict, serverInstance=None, serverMetadata=None, clientInstance=None, clientMetadata=None):
    if serverInstance == None:
      log.error('Unexpected State: serverInstance cannot be null')
      return

    if resourceType not in seriesDict:
      resourceVal = None
    else:
      resourceVal = seriesDict[resourceType]

    if resourceVal == None:
      resourceMetrics = {}
      globalMetrics = {"global": copy.deepcopy(metricsDict), "other": copy.deepcopy(metricsDict)}
      dominant = None
    else:
      resourceMetrics = {resourceVal: copy.deepcopy(metricsDict)}
      globalMetrics = {"global": copy.deepcopy(metricsDict)}
      dominant = {"name": resourceVal, "count": metricsDict["count"]}

    metric = Metric({
      resourceType: {
        "resource_metrics": resourceMetrics,
        "global_metrics": globalMetrics,
        "dominant": dominant,
        "metadata": metadatas[resourceType],
        "name": names[resourceType]
      }
    })

    # update resource metrics on the server
    self.findOrCreateInstance(serverInstance, serverMetadata, inMetric=metric, updateOnlyResourceMetrics=True)

  def finishExternalServicesGraphStage(self, resourceType, response):
    self.profileStage("graph", resourceType)
    log.debug("link index: " + str(self.linkIndex.index) + ", link reverse index: " + str(self.linkIndex.reverseIndex))
    self.commitResourceCompletion()
  ### External Services Graph Stage Ends ###

  ### Health Stage Begins ###
  def healthStage(self):
    log.debug("healthStage")

    nodeIds = self.nodes.keys()
    for nodeId in nodeIds:
      node = self.nodes[nodeId]

      # no health computation for fine grained nodes
      if node.nodeType != "coarse_grained":
        continue

      # find tag key in node metadata and add to node.subgroupTagsFilterMap
      instanceMetadata = node.instance.metadata
      if not instanceMetadata: # nothing to do
        continue

      for tagKey in self.groupByAndFilterTags:
        if tagKey in instanceMetadata and instanceMetadata[tagKey] is not None:
          node.addInfraTag(tagKey, tagValue=instanceMetadata[tagKey], unTagged=False)
        else:
          if nodeId != coarseGrainedMergedNodeId: # don't add tagged for coarse grained merged nodes
            node.addInfraTag(tagKey, tagValue="", unTagged=True)

      if node.getName() is not USER_NODE_NAME:
        nodeGroupSet = frozenset((v["column"].split(".", 1)[1], v["value"]["text"]) for v in node.getGroupValue())

        def isGroupTupleAtomic(tup):
          return tup[0] in ['pod_name', 'container_name', 'host_name']

        def groupSetIsIncluded(small, big):
          # small is in big, or an atomic part of small is in big
          return (small <= big) or any([tup in big for tup in small if isGroupTupleAtomic(tup)])

        matchingGroupSetsHealth = [(groupSet, health) for (groupSet, health) in self.triggeredGroupsHealthMap.iteritems() if groupSetIsIncluded(nodeGroupSet, groupSet)]

        matchingGroupSetsEvent = [(groupSet, event) for (groupSet, event) in self.triggeredGroupsToEvent.iteritems() if groupSetIsIncluded(nodeGroupSet, groupSet)]

        # health is the max of the status of the alerts that are
        # grouped by a superset of the node groupBy set (i.e. alerts grouped more specifically)
        node.inMetric.resourceHealth = max([health for (_, health) in matchingGroupSetsHealth] or [NORMAL])

        # triggers is the union of all triggers of the alerts that are
        # grouped by a superset of the node groupBy set (i.e. alerts grouped more specifically)
        nodeEvents = list(itertools.chain(*[event for (_, event) in matchingGroupSetsEvent]))

        # dedupe triggerIds and alertIds
        node.triggerIds = list(set([e["triggerId"] for e in nodeEvents]))
        node.alertIds = list(set([e["alertId"] for e in nodeEvents]))

        log.debug("Health Level for Service ID {!s} with node name {!s} is {!s}".format(node.serviceId, node.name, node.inMetric.resourceHealth))
    self.profileStage("health computation")
    self.clusterStage()

  def handleTriggerIdResponse(self, seriesDict, metricsDict, triggerId=None, groupInfo=None, alertConfig=None, severity=None):

    if not triggerId:
      log.warn("Unexpected State: triggerId cannot be " + str(triggerId))
      return

    if not severity in ["warning", "critical", "unknown"]:
      log.warn("Unexpected State: Alert event severity cannot be " + str(severity))
      return

    alertConfigJson = safeJsonLoads(alertConfig)
    alertId = alertConfigJson.get("alertId", "")
    if not alertId:
      log.warn("Unexpected State: alert ID not found")
      return

    groupInfoJson = safeJsonLoads(groupInfo)
    groupSet = frozenset()
    groupBys = groupInfoJson.get("group", {})
    if groupBys:
      # set of key-value tuples, with the key being truncated at the first "." is it is "instance" or "client" or "server"
      groupByList = []
      for k in groupBys.keys():
        column = k.split(".", 1)[0]
        if column in ["instance", "client", "server"]:
          groupByList.append((k.split(".", 1)[1], groupBys[k]))
        else:
          groupByList.append((k, groupBys[k]))
      groupSet = frozenset(groupByList)

    self.triggeredGroupsHealthMap[groupSet] = max(SEVERITY_HEALTH_MAP[severity], self.triggeredGroupsHealthMap.get(groupSet))

    if groupSet not in self.triggeredGroupsToEvent:
      self.triggeredGroupsToEvent[groupSet] = []

    eventInfo = {
      "triggerId": triggerId,
      "alertId": alertId
    }
    self.triggeredGroupsToEvent[groupSet].append(eventInfo)

  def finishTriggerIdResponse(self, response):
    # this marks the completion of "health" resource
    self.commitResourceCompletion()

  ### Health Stage Ends ###


  ### Cluster Stage Begins ###
  def clusterStage(self):
    log.debug("clusterStage")
    if "clustering" in self.queryOptions:
      self.clustering = self.queryOptions["clustering"]
    else:
      self.clustering = False
    self.createClusters()

  def createClusters(self):
    cb = self.noClustering
    cbDone = self.noOp
    if self.clustering == True:
      cb = self.resourceSetClustering
      cbDone = self.resourceSetNames
    else:
      cb = self.noClustering

    nodeIds = self.nodes.keys()
    nodeIds.sort()
    for nodeId in nodeIds:
      node = self.nodes[nodeId]

      # skip clustering user node and merged node
      if nodeId in [userNodeId, mergedNodeId]:
        continue

      superNodeId = cb(nodeId, node)
      if superNodeId != -1:
        # merge nodes
        superNode = self.nodes[superNodeId]
        superNode.merge(node)
        del self.nodes[nodeId]
        # merge links
        self.linkIndex.merge(superNodeId, nodeId)
    cbDone()

    self.profileStage("clustering")

    self.visualizationStage()
  ### Cluster Stage Ends ###


  ### Visualization Stage Begins ###
  def visualizationStage(self):
    log.debug("visualizationStage")

    def eliminateRedundantTags(node):
      if not node.resourceKey or node.resourceKey == '{}':
        return

      if not self.groupByAndFilterTags:
        return

      if node.nodeType != "coarse_grained":
        return

      # get the tagsMap for this node
      tagsMap = self.tagsByResourceKey[node.resourceKey]

      # for each tag
      for tagKey in tagsMap:
        if len(tagsMap[tagKey]) == 1:
          for isUnTagged in tagsMap[tagKey]: # only one element in set
            if isUnTagged == True:
              node.removeInfraTag(tagKey)
        else:
          # we have different values for this tag, so nothing to remove
          pass

      # remove from subgroupTagsFilterMap the tags that exists only in filter
      for tagKey in self.filterTags:
        if tagKey not in self.groupByTags:
          node.removeInfraTag(tagKey)

    # nodes
    nodes = {}
    for nodeId, node in self.nodes.iteritems():
      if nodeId == userNodeId and node.empty():
        # skip user node if empty
        log.debug("skip user node; its empty")
        continue

      if nodeId == mergedNodeId and node.empty():
        # skip merged node if empty
        log.debug("skip merged node; its empty")
        continue

      eliminateRedundantTags(node)

      if node.serviceId == -1:
        node.createNodeSignature(self.remainingNodesBehavior)

      if node.nodeType in ["coarse_grained"]:
        node.addInfraFilter(self.instanceUserFilter)

        # for merged coarse grained node, add not remote filter to signature
        # TODO: remove hack
        if not self.groupByTags:
          containerFilter = {
            "type":"match",
            "column":"instance.instance_type",
            "value":{
              "text":"container"
            }
          }

          podFilter = {
            "type":"match",
            "column":"instance.instance_type",
            "value":{
              "text":"pod"
            }
          }

          hostFilter = {
            "type":"match",
            "column":"instance.instance_type",
            "value":{
              "text":"host"
            }
          }

          if "instance_type" in node.userFilterMap:
            node.userFilterMap["instance_type"].append([containerFilter, podFilter, hostFilter])
          else:
            node.userFilterMap["instance_type"] = [containerFilter, podFilter, hostFilter]

      nodeJson = node.serialize()
      nodes[nodeId] = nodeJson

    # links
    links = []
    for clientId, serversIndex in self.linkIndex.index.index.iteritems():
      for serverId, link in serversIndex.iteritems():
        linkJson = link.serialize()
        linkJson["source"] = clientId
        linkJson["target"] = serverId
        linkJson["id"] = str(clientId) + "-TO-" + str(serverId)
        links.append(linkJson)

    self.returnTopologyResponse(nodes, links)
    self.profileStage("visualization")

  def returnTopologyResponse(self, nodes, links, error=None):
    if error:
      self.set_status(400)
      self.write(str(error))
    else:
      topologyJson = {"nodes": nodes, "links": links}
      self.write(json.dumps(topologyJson))

    self.flush()
    self.finish()
    self.aborted = True
    return
  ### Visualization Stage Ends ###

  def commitResourceCompletion(self):
    '''
    increment resource progress counter -- the following clause is atomic as aync
    callbacks are scheduled on mainLoop
    '''
    self.resourceProgressCounter = self.resourceProgressCounter + 1
    if self.resourceProgressCounter == len(self.resourceDeque):
      log.debug("have processed all resourceTypes, go to next component")
      self.healthStage()

  ''' Topology Processing Pipeline Ends '''

  def findOrCreateInstance(self, instanceId, metadataStr, nodeType=None, inMetric = None, outMetric = None, infraMetric=None, updateOnlyResourceMetrics=False):
    metadata = {}
    if metadataStr != "":
      metadata = safeJsonLoads(metadataStr)

    if instanceId not in self.nodes:
      # create instance
      instance = Instance(metadata, instanceId)
      self.nodes[instanceId] = Node(instance, nodeType, inMetric, outMetric, infraMetric)
    else:
      # update node metrics
      node = self.nodes[instanceId]
      node.updateInMetric(inMetric, updateOnlyResourceMetrics)
      node.updateOutMetric(outMetric, updateOnlyResourceMetrics)
      node.updateInfraMetric(infraMetric, updateOnlyResourceMetrics)
    return True

  def linkInstances(self, clientInstanceId, serverInstanceId, metric):
    newLink = Link(metric, serverInstanceId)
    self.linkIndex.link(clientInstanceId, serverInstanceId, newLink)

  def noClustering(self, nodeId, node):
    instance = node.instances[0]
    node.setName(instance.name)
    return -1

  def belongsToKnownCohort(self, nodeId, node):
    log.debug("SERVICE COHORTS: " + json.dumps(self.serviceCohorts))
    if not self.serviceCohorts:
      return (False, [])
    isBelong = False
    serviceIds = []
    for (sId, cohort) in self.serviceCohorts.iteritems():
      for instance in cohort:
        if instance["instance"] == nodeId:
          serviceIds.append(sId)
          isBelong = True
    return (isBelong, serviceIds)

  def resourceSetClustering(self, nodeId, node):
    if node.nodeType == "fine_grained":
      if node.inMetric.empty():
        log.warn("Unexpected State: no in metric found for fine grained remote server node")
        return -1
      resourcesDict = self.inResources
      resourceMetric = node.inMetric
      isServer = True
      resourceType = resourceMetric.getResourceType()

      # we couldn't find a matching resourceType
      if not resourceType:
        return -1

      # get the dominant resource for this node
      dominantResource = node.getDominantResource(resourceType, resourceMetric)

      if self.remainingNodesBehavior == "merge":
        resources = self.mergedResources
      else:
        # search the list of all resources to see if we find a match
        resources = resourcesDict[resourceType]

      resourceKey = self.getResourceKey(node, [], dominantResource, resourceType, isServer)

      if resourceKey in resources:
        # return the nodeId if we have a match so that we can merge
        return resources[resourceKey]
      else:
        if self.remainingNodesBehavior == "merge":
          if not self.groupByTags:
            # TODO: Do we need a special treatment for merged nodes without subgroups ?
            resources[resourceKey] = mergedNodeId
            return mergedNodeId
          else:
            resources[resourceKey] = nodeId
            return -1
        else:
          # add new dominant resource
          resources[resourceKey] = nodeId
          return -1
    elif node.nodeType == "coarse_grained":
      resourceKey = self.getResourceKey(node, [], None, None, None)
      if resourceKey in self.coarseGrainedNodes:
        return self.coarseGrainedNodes[resourceKey]
      else:
        self.coarseGrainedNodes[resourceKey] = nodeId
        return -1
    else:
      return -1

  def resourceSetNames(self):
    for nodeId, node in self.nodes.iteritems():
      if node.nodeType == "coarse_grained":
        continue
      elif node.nodeType == "user_node":
        node.setName(USER_NODE_NAME)
      elif node.nodeType == "merged_node":
        node.setName(MERGED_NODE_NAME)
      else:
        if self.remainingNodesBehavior == "merge":
          node.setName(MERGED_NODE_NAME)
        else:
          if not node.inMetric.empty():
            resourceCount = 0
            resourceType = node.inMetric.getResourceType()
            resourceMetrics = node.inMetric.resourceDict.get(resourceType, {}).get('resource_metrics', {})
            if resourceMetrics:
              resourceCount = len(resourceMetrics.keys()) - 1

            moreString = ''
            if resourceCount != 0:
              moreString = ' (+' + str(resourceCount) + ' more)'

            node.setName(node.inMetric.name() + moreString)
          else:
            node.setName("Internal Client")

  def noOp(self):
    pass

  def getResourceKey(self, node, serviceIds=[], resource=None, resourceType=None, isServer=None):

    # construct the key
    if node.nodeType == "fine_grained":
      if self.remainingNodesBehavior == "merge":
        resourceKey = {
          "mergedNodeId": mergedNodeId
        }
      else:
        # auto-grouped
        resourceKey = {
          "autogroupId": {
            "resource": resource,
            "resourceType": resourceType,
            "isServerNode": isServer
          }
        }
      node.resourceKey = json.dumps(resourceKey)
    else:
      resourceKey = {}
      instanceMetadata = node.instance.metadata
      if not instanceMetadata: # nothing to do
        log.error("Unexpected state: no metadata for coarse grained node")

      for tagKey in self.groupByTags:
        tagValue = instanceMetadata.get(tagKey, "")
        resourceKey[tagKey] = tagValue

      node.resourceKey = json.dumps(resourceKey)

      # this helps identifies if some redundant tags need to be eliminated
      # i.e., some tag which appears in all nodes for this resource Key
      for tagKey in self.groupByTags:
        if tagKey in instanceMetadata:
          unTagged = False
        else:
          unTagged = True

        # populate the tags
        if node.resourceKey not in self.tagsByResourceKey:
          self.tagsByResourceKey[node.resourceKey] = {}

        if tagKey not in self.tagsByResourceKey[node.resourceKey]:
          self.tagsByResourceKey[node.resourceKey][tagKey] = Set([])

        self.tagsByResourceKey[node.resourceKey][tagKey].add(unTagged)

    return node.resourceKey

def responseCompletePreCb(self, responseCompleteCb, requestBody, response):
  responseCompleteCb(response)

def requestData(self, dataSource, requestBody, handleTupleCb, responseCompleteCb):
  if self.aborted:
    log.info('do not make new requests, this handler was aborted for further computation')
    return

  httpRequest = HTTPRequest(url = DATASTORE + dataSource, method='POST', headers={'x-organization-id': self.organization_id}, body=json.dumps(requestBody), request_timeout=QUERY_TIMEOUT)
  http_client = AsyncHTTPClient()
  http_client.fetch(httpRequest, partial(handleData, self, handleTupleCb, responseCompleteCb, DATASTORE + dataSource, requestBody))

def handleData(self, handleTupleCb, responseCompleteCb, url, requestBody, response):
  if self.aborted:
    log.info('discard analytics response data, this handler was aborted for further computation')
    return
  data = response.body
  data_json = safeJsonLoads(data)

  if response.error:
    log.error("Error: " + str(response.error))
    log.error("Body: " + str(response.body))
    self.set_status(500)
    self.write(json.dumps({'error_message': 'Analytics query failed, add filters or reduce time range'}))
    self.flush()
    self.finish()
    self.aborted = True
    return

  data_tuples = data_json.get("data", [])
  iterateResponse(self, handleTupleCb, responseCompleteCb, requestBody, response, data_tuples)

def iterateResponse(self, handleTupleCb, responseCompleteCb, requestBody, response, data_tuples):
  for data_tuple in data_tuples:
    if self.aborted:
      log.info('discard analytics response data, this handler was aborted for further computation')
      return
    self.stat_counter = self.stat_counter + 1
    if self.stat_counter >= 100:
      self.apiServer.processHighPrioEvent()
      self.apiServer.stat_counter = 0
    args = {}
    metricsDict = {}
    seriesDict = {}
    if "instance.id" in data_tuple:
      args["serverInstance"] = data_tuple["instance.id"]

    if "instance" in data_tuple:
      args["serverMetadata"] = data_tuple["instance"]

    if "server" in data_tuple:
      args["serverMetadata"] = data_tuple["server"]

    if "client" in data_tuple:
      args["clientMetadata"] = data_tuple["client"]

    ''' HEALTH FIELDS BEGINS '''

    if "trigger_id" in data_tuple:
      args["triggerId"] = data_tuple["trigger_id"]

    if "group_info" in data_tuple:
      args["groupInfo"] = data_tuple["group_info"]

    if "alert_config" in data_tuple:
      args["alertConfig"] = data_tuple["alert_config"]

    if "severity" in data_tuple:
      args["severity"] = data_tuple["severity"]

    ''' HEALTH FIELDS ENDS '''

    # get group by
    serverMetadata = {}
    clientMetadata = {}

    for key, value in data_tuple.iteritems():
      if key.startswith("server."):
        serverMetadata[key.split("server.", 1)[1]] = value
      elif key.startswith("instance."):
        serverMetadata[key.split("instance.", 1)[1]] = value
      elif key.startswith("client."):
        clientMetadata[key.split("client.", 1)[1]] = value
      else:
        pass

    # TODO: don't json dumps here - pass around dict within python
    if "server.id" in data_tuple:
      args["serverInstance"] = data_tuple["server.id"]
    else:
      if serverMetadata:
        args["serverMetadata"] = json.dumps(serverMetadata)
        args["serverInstance"] = args["serverMetadata"]

    if clientMetadata:
      args["clientMetadata"] = json.dumps(clientMetadata)
      args["clientInstance"] = args["clientMetadata"]

    # resources
    for resourceType, resourceCol in RESOURCES.iteritems():
      if resourceCol in data_tuple:
        seriesDict[resourceType] = data_tuple[resourceCol]
        # we found cases where a resource like http.uri (CONNECT) or dns.domain could be null
        # construct a synthetic value to represent that
        if not seriesDict[resourceType]:
          seriesDict[resourceType] = "null"

    # metrics
    for metricType, aggregate in metricTypeToAggregate.iteritems():
      if aggregate in data_tuple:
        metricsDict[metricType] = data_tuple[aggregate]

    if args != {} or metricsDict != {} or seriesDict != {}:
      try:
        handleTupleCb(seriesDict, metricsDict, **args)
      except:
        log.warn("callback exception", exc_info=full_exc_info())
  responseCompletePreCb(self, responseCompleteCb, requestBody, response)

def safeJsonLoads(data):
  try:
    return json.loads(data)
  except:
    return {}