from utils.request_handlers import WebRequestHandler, log_close_webrequest_exception
import zlib
import math
import ujson as json
import tornado.web
import tornado.ioloop
from utils import global_consts
from functools import partial
from proto import *
import os, os.path
import tornado.httpclient
import logging
log = logging.getLogger('Monitor.ApiReceiverHandler')
SP_LB_HOST = str(os.getenv('SP_LB_HOST', '127.0.0.1'))
SP_LB_PORT = str(os.getenv('SP_LB_PORT', '5005'))
IS_HA = str(os.getenv('IS_HA', 'no'))
LOAD_TEST_MESSAGE_REPEAT_ITERATIONS = int(os.getenv('LOAD_TEST_MESSAGE_REPEAT_ITERATIONS', 1))
client = tornado.httpclient.AsyncHTTPClient()
# datadog handler endpoints
DOGSTATSD_ENDPOINT = r"/api/v1/"
METRICS_ENDPOINT = r"/intake/"
STATUS_ENDPOINT = r"/status"
INSTANCE_METADATA_ENDPOINT = r"/instance_metadata"
INSTANCE_METADATA_BULK_ENDPOINT = r"/instance_metadata_bulk"
TUPLES_ENDPOINT = r"/tuples"
TUPLES_API_VERSION = 'v2'
# splb proxy endpoints
CONNECT_ENDPOINT = r"/connect"
INSTALL_EPOCH_COLLECTORS_ENDPOINT = r"/install-epoch-collectors"
GAUGE = 'gauge'
RATE = 'rate'
COUNT = 'count'
dogstatsd_types = [GAUGE, RATE, COUNT]
# first value in tuple to scanalytics needs to be string of location specifier - can be empty
LOCATION_SPECIFIER = "metrics_handler"
# the endings that datadog appends to metrics in a histogram
hist_endings = [".max", ".avg", ".median", ".count", ".95percentile"]
# DataDog Agent Handler
class ApiReceiverHandler(WebRequestHandler):
  """
  #Removed @oas for now, since the url is not supported in frontend yet. This block will be ignored. Also removed the "metric" tag from swagger_init.json.
  [post] /api/v1/series/{api_key}
    "tags": ["metric"],
    "description": "Post time-series data",
    "operationId": "series",
    "parameters":[
      {
        "name": "api_key",
        "in": "path",
        "description": "ID of the organization",
        "required": true,
        "schema": {
          "type": "string"
        }
      }
    ],
    "requestBody": {
      "content": {
        "application/json": {
          "schema": {
            "$ref": "#/components/schemas/Series"
          }
        }
      }
    },
    "responses": {
      "200": {
        "description": "OK"
      }
    }
  """
  """
  #Removed @oas for now, since the url is not supported in frontend yet. This block will be ignored. Also removed the "event" tag from swagger_init.json.
  [post] /api/v1/intake/{api_key}
    "tags": ["event"],
    "description": "Post events",
    "operationId": "intake",
    "parameters":[
      {
        "name": "api_key",
        "in": "path",
        "description": "ID of the organization",
        "required": true,
        "schema": {
          "type": "string"
        }
      }
    ],
    "requestBody": {
      "content": {
        "application/json": {
          "schema": {
            "$ref": "#/components/schemas/Event"
          }
        }
      }
    },
    "responses": {
      "200": {
        "description": "OK"
      }
    }
  """
  @tornado.web.asynchronous
  def get(self, v=None):
    if self.is_endpoint(STATUS_ENDPOINT):
      code = 200
      self.set_status(code)
      self.finish()
  @tornado.web.asynchronous
  def post(self, v=None):
    code = 200
    try:
      for i in range(LOAD_TEST_MESSAGE_REPEAT_ITERATIONS):
        if self.is_endpoint(DOGSTATSD_ENDPOINT):
          self.apiServer.scheduleEvent(self.parse_dogstatsd2, global_consts.MAX_EVENT_PRIO - 3)
        elif self.is_endpoint(METRICS_ENDPOINT):
          self.apiServer.scheduleEvent(self.parse_metrics_and_events, global_consts.MAX_EVENT_PRIO - 3)
        elif self.is_endpoint(INSTANCE_METADATA_BULK_ENDPOINT):
          self.apiServer.scheduleEvent(self.inject_metadata_bulk, global_consts.MAX_EVENT_PRIO - 3)
        elif self.is_endpoint(INSTANCE_METADATA_ENDPOINT):
          self.apiServer.scheduleEvent(self.inject_metadata, global_consts.MAX_EVENT_PRIO - 3)
        elif self.is_endpoint(TUPLES_ENDPOINT):
          if TUPLES_API_VERSION in self.request.uri:
            self.apiServer.scheduleEvent(self.inject_tuples, global_consts.MAX_EVENT_PRIO - 3)
          else:
            code = 400
            log.error("Version mismatch. Running version: {!s}".format(TUPLES_API_VERSION))
        else:
          code = 404
          log.error("404 not found. Tried to access endpoint: {!s}".format(self.request.uri))
    except Exception as err:
      import traceback, sys
      exc_info = sys.exc_info()
      #tgill: always return 200 in order to prevent re-tries from the client
      code = 200
      log.exception("Encountered error: " + str(err))
      traceback.print_exception(*exc_info)
      del exc_info
    finally:
      self.set_status(code)
      self.finish()
  def is_endpoint(self, endpoint):
    return endpoint in self.request.uri
  def parse_dogstatsd2(self):
    body = self.request.body
    # unzip the body if header content-encoding says deflate
    if self.request.headers.get("Content-Encoding") == "deflate":
      body = zlib.decompress(body)
    bodyJson = json.loads(body)
    orgId = self.request.query
    if IS_HA == 'yes' and not orgId:
      log.warn('Received an empty Organization ID')
    if orgId.startswith("api_key="):
      orgId = orgId[8:]
    is_restricted = False
    if not isinstance(bodyJson, dict):
      # list returns error status from dd
      return
    host = ''
    series = bodyJson.get('series', [])
    if len(series) > 0:
      serie = series[0]
      host = serie.get('host')
      is_restricted = self.apiServer.isHostRestricted(orgId, host)
    if not is_restricted:
      self.apiServer.sendDogStatsd(
        [LOCATION_SPECIFIER, orgId, body]
      )
    else:
      log.info('Host ' + str(host) + ' is restricted, not sending stats')
  def parse_and_send_stat(self, stat, q):
    if self.apiServer.stat_counter >= 100:
      self.apiServer.processHighPrioEvent()
      self.apiServer.stat_counter = 0
    self.parse_and_send_stat_task(stat, q)
    self.apiServer.stat_counter = self.apiServer.stat_counter + 1
  def parse_and_send_stat_task(self, stat, q):
    name = str(stat.get("metric"))
    stat_type = stat.get("type")
    tags = stat.get("tags")
    if tags is None:
      tags = []
    if stat.get("device_name") is not None:
      tags.append("device_name:{!s}".format(stat.get("device_name")))
    if stat.get("host") is not None:
      tags.append("host:{!s}".format(stat.get("host")))
    if stat.get("source") is not None:
      tags.append("source:{!s}".format(stat.get("source")))
    json_tags = self.parse_tags(tags)
    timestamp, value = stat.get("points")[0]
    timestamp = (int)(timestamp/q)*q
    if stat_type == RATE:
      interval_sec = stat.get("interval")
      if interval_sec is not None:
        value = value*interval_sec
    orgId = self.request.query
    if orgId.startswith("api_key="):
      orgId = orgId[8:]
    #dogtatsd_counter(@N, orgId, STATSD_KEY, STATSD_TAGS, COUNT=1, SUM=real_val, MAX=real_val, MIN=real_val, SQUARED_SUM=val^2, TIMESTAMP=dogstatsd_timestamp),
    try:
      f_value = float(value)
      self.apiServer.sendDogStatsdCounter(
        [LOCATION_SPECIFIER, orgId, name, json_tags, 1, f_value, f_value, f_value, math.pow(f_value, 2), timestamp]
      )
    except TypeError as e:
      log.exception("Error: {!s}\nValue:{!s} : Type(Value):{!s}\n".format(e, value, type(value)))
  #@do_cprofile
  def parse_metrics_and_events(self):
    body = self.request.body
    # unzip the body if header content-encoding says deflate
    if self.request.headers.get("Content-Encoding") == "deflate":
      body = zlib.decompress(body)
    body = json.loads(body)
    orgId = self.request.query
    if IS_HA == 'yes' and not orgId:
      log.warn('Received an empty Organization ID')
    if orgId.startswith("api_key="):
      orgId = orgId[8:]
    # parse the individual machine metrics
    timestamp = body.get('collection_timestamp')
    host = body.get('meta', {}).get('hostname') or body.get('internalHostname')
    source = body.get('source', '')
    load_metrics = ['system.load.1', 'system.load.5', 'system.load.15',
                    'system.load.norm.1', 'system.load.norm.5', 'system.load.norm.15']
    system_metrics = ['system.uptime']
    cpu_metrics = ['cpuUser', 'cpuSystem', 'cpuWait', 'cpuIdle', 'cpuStolen', 'cpuGuest']
    memory_metrics = ['memBuffers', 'memCached', 'memPageTables', 'memPhysFree',
                      'memPhysPctUsable', 'memPhysTotal', 'memPhysUsable', 'memPhysUsed',
                      'memShared', 'memSlab', 'memSwapCached', 'memSwapFree',
                      'memSwapPctFree', 'memSwapTotal', 'memSwapUsed']
    is_restricted = self.apiServer.isHostRestricted(orgId, host)
    if is_restricted:
      log.info('Host ' + str(host) + ' is restricted, not sending metrics')
      return
    log.debug("metrics and events body: " + str(body))
    # parse the metrics sent over (from checks.d integrations)
    self.parse_metrics(body.get('metrics', []), source)
    # parse the events information (title/text entries)
    events = body.get('events', {})
    #events = events.get('api', [])
    self.parse_events(events, source)
    for metric in load_metrics + system_metrics + cpu_metrics + memory_metrics:
      if body.get(metric) is not None:
        self.parse_and_send_stat({
          'metric': metric,
          'type': GAUGE,
          'host': host,
          'source': source,
          'points': [(timestamp, body.get(metric))]
        }, 20)
    # IO stats
    iostats = body.get('ioStats', {})
    for device, metrics in iostats.items():
      for metric, value in metrics.items():
        if not str(metric).startswith("system.io"):
          metric = "system.io.{!s}".format(metric)
        self.parse_and_send_stat({
          'metric': metric,
          'type': GAUGE,
          'host': host,
          'source': source,
          'points': [(timestamp, value)],
          'tags': ["device_name:{!s}".format(device)]
        }, 20)
  def parse_metrics(self, metrics, source):
    # create stats from metrics section
    for metric in metrics:
      stat = {}
      name, timestamp, value, attrs = metric
      stat['metric'] = name
      stat['points'] = [(timestamp, value)]
      stat['source'] = source
      stat_type = attrs.get('type', GAUGE)
      if 'type' in attrs:
        del attrs['type']
      stat['type'] = stat_type
      if 'hostname' in attrs:
        stat['host'] = attrs.get('hostname')
        del attrs['hostname']
      if 'device_name' in attrs:
        stat['device_name'] = attrs.get('device_name')
        del attrs['device_name']
      if 'tags' in attrs:
        tags = attrs.get('tags')
        del attrs['tags']
      else:
        tags = []
      for key, val in attrs.items():
        tags.append("{!s}:{!s}".format(key, val))
      stat['tags'] = tags
      self.parse_and_send_stat(stat, 20)
  def parse_event(self, event, source):
    #                            {   u'host': u'markus-macbook.epoch.nutanix.com',
    #                                u'msg_text': u'A friend warned me earlier.',
    #                                u'msg_title': u'There might be a storm tomorrow',
    #                                u'timestamp': 1459300891},
    #                            {   u'aggregation_key': u'urgent',
    #                                u'alert_type': u'error',
    #                                u'host': u'markus-macbook.epoch.nutanix.com',
    #                                u'msg_text': u'The city is paralyzed!',
    #                                u'msg_title': u'SO MUCH SNOW',
    #                                u'tags': [u'endoftheworld', u'urgent'],
    #                                u'timestamp': 1459300891},
    # create stats from the events section
    priority = str(event.get('priority', ''))
    host = str(event.get('host',''))
    msg_title = str(event.get('msg_title',''))
    msg_text = str(event.get('msg_text',''))
    timestamp = int(event.get('timestamp',''))
    tags = event.get('tags')
    alert_type = str(event.get('alert_type',''))
    event_type = str(event.get('event_type',''))
    source_type_name = str(event.get('source_type_name',''))
    if tags is None:
      tags = []
    if event.get("host") is not None:
      tags.append("host:{!s}".format(host))
    tags.append("source:{!s}".format(source))
    json_tags = self.parse_tags(tags)
    #dogstatsd_event(@N, ORG_ID, EVENT_NAME, EVENT_MESSAGE, EVENT_TYPE, ALERT_TYPE, SOURCE_TYPE_NAME, DOGSTATSD_TAGS, COUNT, TIMESTAMP_DD)
    orgId = self.request.query
    if orgId.startswith("api_key="):
      orgId = orgId[8:]
      self.apiServer.sendDogStatsdEvent(
        [LOCATION_SPECIFIER, orgId, msg_title, msg_text, event_type, alert_type, source_type_name, json_tags, 1, timestamp]
      )
  def parse_events(self, all_events, source):
    '''
    all_events looks like this:
    {
      docker_daemon: [ {...}, {...} ],
      kubernetes: [ {...}, {...} ],
      ...
    }
    '''
    for integration, events in all_events.iteritems():
      for event in events:
        self.parse_event(event, source)
  def parse_tags(self, tags):
    # tags is a list of strings with "key:val"
    keyval_tags = {}
    if tags is not None:
      for tag in tags:
        if ":" in tag:
          key, val = tag.split(":", 1)
        else:
          key = tag
          val = ""
        if val != "":
          vals = keyval_tags.get(key, [])
          vals.append(val)
          keyval_tags[key] = vals
        else:
          keyval_tags[key] = []
    # create the json string format for the tags
    return json.dumps(keyval_tags)
  def sendMetadataTuple(self, orgId, hostname, source, namespace, bodyStr):
    isAgent = False
    if source == '':
      # all old collectors are agents
      isAgent = True
    else:
      if 'coll_arch:agentless' not in source:
        # Forward metadata from api receiver to splb only for coll_arch:agent
        isAgent = True
    if source == '':
      # 'source' was not present in the older version of collectors
      # we use the hostname here as source here to maintain backward
      # compatibility
      source = hostname
    # send metadata to splb to sync with zk
    if isAgent:
      if self.request.headers.get("Content-Encoding") == "deflate":
        bodySPLB = zlib.compress(bodyStr)
      else:
        bodySPLB = bodyStr
      req = tornado.httpclient.HTTPRequest ('http://' + str(SP_LB_HOST) + ':' + str(SP_LB_PORT) + '/metadata', headers=self.request.headers, body=bodySPLB, method='POST')
      client.fetch(req)
    is_restricted = self.apiServer.isHostRestricted(orgId, hostname)
    if not is_restricted:
      # inject source_metadata_reliable tuple into the pipeline
      self.apiServer.sendTuple(
        "source_metadata_reliable",
        [LOCATION_SPECIFIER, orgId, source, bodyStr]
      )
    else:
      log.info('Host ' + str(source) + ' is restricted, not sending metadata tuple')
  # Deprecated, here because of backward compatibility
  def inject_metadata(self):
    body = self.request.body
    # unzip the body if header content-encoding says deflate
    if self.request.headers.get("Content-Encoding") == "deflate":
      body = zlib.decompress(body)
    metadata = json.loads(body)
    # cast as str to impose utf-8 encoding
    orgId  = str(metadata.get('organization_id', 'epoch'))
    namespace = str(metadata.get('network_namespace', 'epoch'))
    hostname = str(metadata.get('host_name', 'epoch'))
    self.sendMetadataTuple(orgId, hostname, '', namespace, body)
  def inject_metadata_bulk(self):
    try:
      body = self.request.body
      # unzip the body if header content-encoding says deflate
      if self.request.headers.get("Content-Encoding") == "deflate":
        body = zlib.decompress(body)
      metadataList = json.loads(body)['metadataList']
      for meta in metadataList:
        orgId = str(meta.get('organization_id', 'epoch'))
        hostname = str(meta.get('host_name', 'epoch'))
        source = str(meta.get('source', ''))
        namespace = str(meta.get('network_namespace', 'epoch'))
        bodyStr = json.dumps(meta)
        self.sendMetadataTuple(orgId, hostname, source, namespace, bodyStr)
    except Exception as err:
      log.exception('Error: ' + str(err))
  def inject_tuples(self):
    body = self.request.body
    host_name = self.request.headers.get("x-host-name")
    org_id = self.request.headers.get("x-organization-id")
    # sync with collectors and check if hostname is restricted
    is_restricted = self.apiServer.isHostRestricted(org_id, host_name)
    if not is_restricted:
      # unzip the body if header content-encoding says deflate
      if self.request.headers.get("Content-Encoding") == "deflate":
        body = zlib.decompress(body)
      self.apiServer.sendRawPayload(body)
    else:
      log.info('Host ' + str(host_name) + ' is restricted, not sending tuples')
class SpLbProxyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, v=None):
      if INSTALL_EPOCH_COLLECTORS_ENDPOINT in self.request.uri:
        req = tornado.httpclient.HTTPRequest('http://' + str(SP_LB_HOST) + ':' + str(SP_LB_PORT) + '/install-epoch-collectors', method=self.request.method)
        client.fetch(req, self.callback)
      else:
        code = 404
        log.error("404 not found. Tried to access endpoint: {!s}".format(self.request.uri))
        self.set_status(code)
        self.finish()
    @tornado.web.asynchronous
    def post(self, v=None):
        if CONNECT_ENDPOINT in self.request.uri:
          req = tornado.httpclient.HTTPRequest('http://' + str(SP_LB_HOST) + ':' + str(SP_LB_PORT) + '/connect' , body=self.request.body, method=self.request.method)
          client.fetch(req, self.callback)
        else:
          code = 404
          log.error("404 not found. Tried to access endpoint: {!s}".format(self.request.uri))
          self.set_status(code)
          self.finish()
    def callback(self,response):
        try:
            self.set_status(response.code)
            self.write(str(response.body))
        finally:
            self.finish()
class SpLbInfoHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, v=None):
        req = tornado.httpclient.HTTPRequest ( 'http://' + str(SP_LB_HOST) + ':' + str(SP_LB_PORT) + '/collectorinfo', body = self.request.body, method = self.request.method )
        client.fetch(req, self.callback)
    def callback(self, response):
        try:
            self.set_status(response.code)
            self.write(str(response.body))
        finally:
            self.finish()
class SpLbCrashHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, v=None):
        req = tornado.httpclient.HTTPRequest ( 'http://' + str(SP_LB_HOST) + ':' + str(SP_LB_PORT) + '/crash', body = self.request.body, method = self.request.method )
        client.fetch(req, self.callback)
    def callback(self, response):
        try:
            self.set_status(response.code)
            self.write(str(response.body))
        finally:
            self.finish()