mport pdb
import os
from functools import partial
from utils import global_consts

from io import BytesIO
import json
from utils import protobuf_json

from lxml import etree
import xmltodict

import tornado.escape
from tornado.escape import json_encode
import tornado.web

from kazoo.client import KazooClient
from kazoo.retry import KazooRetry
from kazoo.client import KazooState
from kazoo.recipe.watchers import ChildrenWatch

from utils import util_functions
from utils.util_functions import full_exc_info
from utils.request_handlers import WebRequestHandler, log_close_webrequest_exception
import re

from collections import OrderedDict
import copy

from twisted.internet.task import LoopingCall
from proto import *

import logging
import  xml.etree.ElementTree as ET
import time

log = logging.getLogger('Monitor.ConfigurationManager')

ZK_PORT = int(os.environ.get('ZK_PORT', failobj=2181))
ZK_HOST = str(os.environ.get('ZK_HOST', failobj='127.0.0.1'))

ZK_KEEP_ALIVE_PERIOD = 600

APP_POSITION = 5
RESOURCE_POSITION = APP_POSITION + 1

CURRENT_ZK_STATE = None
g_isApiServer = False

g_tables = set()

def kazoo_listener(state):
    global CURRENT_ZK_STATE
    if state == KazooState.LOST:
        # Register somewhere that the session was lost
        if CURRENT_ZK_STATE == KazooState.SUSPENDED:
          log.error("SUSPENDED -> LOST: Session expired")
        elif CURRENT_ZK_STATE == KazooState.CONNECTED:
          log.error("CONNECTED -> LOST: Invalid authentication")
        log.info("Lost connection to zookeeper, exit process.")
        CURRENT_ZK_STATE = KazooState.LOST
        import os
        os._exit(1)
    elif state == KazooState.SUSPENDED:
        # Handle being disconnected from Zookeeper
        log.info("Being disconnected from zookeeper")
        CURRENT_ZK_STATE = KazooState.SUSPENDED
    else:
        # Handle being connected/reconnected to Zookeeper
        log.info("Connecting to zookeeper")
        CURRENT_ZK_STATE = KazooState.CONNECTED
        if g_isApiServer:
          zookeeper_resync()
        else:
          agent_resync()

def agent_resync():
  if configManager.parent.localNodeId:
    # resync API server config
    for configValue in configManager.configValues:
      configManager.parent.scheduleThread(configManager.parent.zkThreadId, 0, configValue.configSync)

def zookeeper_resync():
    if configManager.parent.role != "" and configManager.parent.version != "" and configManager.parent.configSet:
        configManager.parent.scheduleThread(configManager.parent.zkThreadId, global_consts.MAX_EVENT_PRIO - 1, configManager.parent.setRoleInfo)
    if configManager.parent.localNodeId:
        # common agent resync
        agent_resync()
        # resync routing info
        configManager.parent.scheduleThread(configManager.parent.zkThreadId, global_consts.MAX_EVENT_PRIO - 1, configManager.parent.setLocalInfo, configManager.parent.localNodeId)
        # resync report dashboard and visualization info
        if hasattr(configManager.parent, 'reportManager'):
            if configManager.parent.reportManager:
                configManager.parent.scheduleThread(configManager.parent.zkThreadId, global_consts.MAX_EVENT_PRIO - 1, configManager.parent.reportManager.initializeReports)
        # Send a config sync request when getting reconnected to zookeeper
        if hasattr(configManager.parent, 'host'):
            configManager.parent.createTool("ConfigSyncReqTool")

g_tableChildren = {}

def zkGet(url, **kwargs):
  if "watch" in kwargs:
    log.debug("adding watch on " + str(url))
    tableChildren = insertTableRow(url)
  return configManager.zkClient.get(url, **kwargs)

def zkGetAsync(url, **kwargs):
  if "watch" in kwargs:
    log.debug("adding watch on " + str(url))
    tableChildren = insertTableRow(url)
  return configManager.zkClient.get_async(url, **kwargs)

def zkSet(url, data, **kwargs):
  if "watch" in kwargs:
    log.debug("adding watch on " + str(url))
    tableChildren = insertTableRow(url)
  return configManager.zkClient.set(url, data, **kwargs)

def zkSetAsync(url, data, **kwargs):
  if "watch" in kwargs:
    log.debug("adding watch on " + str(url))
    tableChildren = insertTableRow(url)
  return configManager.zkClient.set_async(url, data, **kwargs)

def insertTableRow(url):
  #TODO: a lock to handle concurrent inserts/deletes?
  try:
      tokens = url.rsplit("/", 1)
      tableName = tokens[0]
      child = tokens[1]
      if tableName not in g_tableChildren:
        g_tableChildren[tableName] = set()
      g_tableChildren[tableName].add(child)
  except Exception,e:
      log.error("Invalid table url: " + str(url) + " Reason: "+ str(e), exc_info=full_exc_info())

def deleteTableRow(tableName, rowName):
  #TODO: a lock to handle concurrent inserts/deletes?
  try:
      if tableName in g_tableChildren:
        g_tableChildren[tableName].remove(rowName)
  except Exception,e:
      log.error("Invalid table url: " + str(url) + " Reason: "+ str(e), exc_info=full_exc_info())

#Sends the new table row resource to the backend
def updateNewResource(fullUrl, urlData, appId, tableSchema):
    try:
        #Send the new resource name back to process
        newConfigResource = fullUrl.split('/',RESOURCE_POSITION)[RESOURCE_POSITION]
        seqIndex = newConfigResource.rfind('/')
        seqNum = newConfigResource[seqIndex+1:]
        #Send add config resource to process
        params = { "appId": appId,
                   "resources": [{"resourceName" : newConfigResource,
                                  "currentValue": urlData}]}
        configManager.parent.createTool("AddConfigResourceTool", params)
        callback = configManager.zkClient.create_async(
                           fullUrl.replace("config", "config_schema", 1),
                           bytes(tableSchema),
                           makepath=True)
        configManager.zkClient.create_async(
            fullUrl.replace("config", "config_flags", 1),
            bytes({"deleteFlag":True, "isTable":False}),
            makepath=True)
        callback.rawlink(partial(updateWatchers, fullUrl, appId, seqNum))
    except Exception,e:
        log.error("Error sending new table row: " + str(e), exc_info=full_exc_info())

def updateWatchers(fullUrl, appId, seqNum, response):
    configManager.watchers[fullUrl] = [appId]
    zkGetAsync(fullUrl,
               watch=configManager.watchedUpdate)
    #Mark the table row as deletable
    configManager.parent.deletableRsrcs.add(fullUrl)
    #Return the table row uuid
    log.info("Success sending new table row named: " + str(seqNum))

"""
Config Handler
Allows the user to see configuration values for processes from zookeeper.
User may change or delete the value. Note that some values cannot be deleted.
"""
class ConfigHandler(WebRequestHandler):
    def removeResourceTrails(self, url):
        url = url.rsplit("/~xml", 1)[0]
        if self.fullTxnId:
            url = url.rsplit(self.fullTxnId)[0]
        return url

    #Gets the configuration value of the chosen node
    @tornado.web.asynchronous
    def get(self, fullResourceName, fullNodeNameOrGlobal, nodeType, nodeId, appName, resourceName, lastResource, xmlStr, fullTxnId, txnId):
        self.fullTxnId = fullTxnId
        # /fullNodename or /global_configs
        if fullNodeNameOrGlobal == "/global_configs":
            #revert for global!!!
            #zookeeperUrl = "/epoch/global_confs" + self.request.path
            zookeeperUrl = "/epoch/version-"+configManager.parent.version + self.request.path
        else:
            zookeeperUrl = "/epoch/version-" + configManager.parent.version +  self.request.path

        zookeeperUrl = self.removeResourceTrails(zookeeperUrl)
        self.xmlStr = xmlStr
        self.isNodesRetrieval = self.request.path == "/config" or self.request.path == "/config/~xml"
        self.resourceName = resourceName
        self.resource = zookeeperUrl
        # Send request to zookeeper to get config value of node
        if not configManager.zkClient.connected:
            self.write_err("Not connected to zookeeper")
            self.flush()
            self.finish()
        else:
            try:
                self.deletableList = [];
                # Check if it has children or is a table. If it does, it's a table.
                callback = zkGetAsync(self.resource.replace("config", "config_flags", 1))
                callback.rawlink(self.handleIsTable)
            except Exception, e:
                exc_info = full_exc_info()
                log.error("exception", exc_info=exc_info)
                self.write_err(exc_info)
                self.flush()
                self.finish()

    # TODO: need to add handling for the global config
    # 0313

    @log_close_webrequest_exception
    def handleIsTable(self, response):
        data, stat = response.get()
        self.isTable = False
        if data:
            data = eval(data)
            self.isTable = data["isTable"]
        callback = configManager.zkClient.get_children_async(self.resource)
        callback.rawlink(self.getChildrenUpdate)

    @log_close_webrequest_exception
    def getChildrenUpdate(self, response):
        children = response.get()
        self.tableDict = {"resource": {}}
        #Check if the resource is a table. If it is, set a flag
        if self.isTable or children:
            self.tableDict["isTable"] = True
            self.numChildren = len(children)
            if self.numChildren == 0:
                self.write(self.tableDict)
                self.flush()
                self.finish()
            else:
                for child in children:
                    childUrl = self.resource + "/" + child
                    callback = zkGetAsync(childUrl)
                    callback.rawlink(partial(self.getChildData, child, childUrl))
        #Else, it's a normal resource
        else:
            callback = zkGetAsync(self.resource)
            callback.rawlink(self.on_get)

    @log_close_webrequest_exception
    def getChildData(self, child, childUrl, response):
        data, stat = response.get()
        if not self.xmlStr:
          if data:
            data = util_functions.XMLToJSON(data)
        aliasChild = child
        if self.isNodesRetrieval and aliasChild.startswith("node-"):
            if child[5:] in configManager.parent.nodeInfoDict:
                aliasChild = configManager.parent.nodeInfoDict[child[5:]]["alias"]
        self.tableDict["resource"].update({ aliasChild: data })
        #If a child is deletable, add flag to that child too
        if childUrl in configManager.parent.deletableRsrcs:
            self.deletableList.append(child)
        self.numChildren -= 1
        if self.numChildren <= 0:
            if self.deletableList:
                self.tableDict["deletables"] = self.deletableList
            self.write(json_encode(self.tableDict))#tornado.escape.xhtml_escape(xmltodict.unparse(tableDict)))
            self.flush
            self.finish()

    @log_close_webrequest_exception
    def on_get(self, response):
        data, stat = response.get()
        if not self.xmlStr:
          if data:
            data = util_functions.XMLToJSON(data)
        self.write(json_encode({"data": data}))#tornado.escape.xhtml_escape(data))
        self.flush
        self.finish()

    #Validates with the schema and updates zookeeper if success
    @tornado.web.asynchronous
    def post(self, fullResourceName, fullNodeNameOrGlobal, nodeType, nodeId, appName, resourceName, lastResource, xmlStr, fullTxnId, txnId):
        if txnId:
            if txnId not in self.zk_transactions:
                self.write_err("Invalid transaction id")
                self.flush()
                self.finish()
                return
        self.fullTxnId = fullTxnId
        self.txnId = txnId
        if fullNodeNameOrGlobal == "/global_configs":
          #revert for global!!!
          #self.configUrl = "/epoch/global_confs" + self.request.path.rsplit('/~xml')[0]
          self.configUrl = "/epoch/version-" + configManager.parent.version + self.request.path
        else:
          self.configUrl = "/epoch/version-" + configManager.parent.version + "/" + self.request.path
        self.configUrl = self.removeResourceTrails(self.configUrl)
        self.appName = appName[1:]
        self.resourceName = resourceName[1:]
        if "role" in fullNodeNameOrGlobal:
          self.isLocal = False
        else:
          self.isLocal = True
        self.schemaUrl = self.configUrl.replace("config", "config_schema", 1)
        if not configManager.zkClient.connected:
            self.write_err("Not connected to zookeeper")
            self.flush()
            self.finish()
        else:
            try:
                self.data = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(self.request.body)  # (self.request.body)
                self.config = ""
                self.config = str(xmltodict.unparse(self.data))
            except:
                log.warn("exception", exc_info=full_exc_info())
                self.config = self.request.body
            log.debug("xml to be validated is: " + self.config)
            cb = zkGetAsync(self.schemaUrl)
            cb.rawlink(self.validate_config)
            # d = util_functions.getLocalPage(self.request.path.replace("config", "config_schema", 1), configManager.parent.webPort)
            # d.addCallback(self.validate_config)

    @log_close_webrequest_exception
    def validate_config(self, response):
        data, stat = response.get()
        self.tableSchema = data
        schema = etree.XMLSchema( etree.XML(self.tableSchema) )
        userConfigs = etree.parse(BytesIO(self.config))
        if schema.validate(userConfigs):
            #If the resource is a table, add new rows to it
            if self.resourceName in configManager.tables:
                self.createSequenceNode(self.config, self.txnId)
            #Else, update the resource at the url
            else:
                #Check if there is a config primary key. If there is,
                #if it differs from the resource name, delete one and create new url
                self.newPrimaryKey = ""
                match = re.search('(?<=config_primary_key>).+(?=</config_primary_key)', self.config)
                if match:
                    self.newPrimaryKey = match.group(0)
                #If key is different
                if self.newPrimaryKey and not self.resourceName.endswith(self.newPrimaryKey):
                    bareResourceName = self.resourceName.split("/")[-1]
                    tableName = self.resourceName.split("/")[0]
                    #url reverse replace
                    updatedConfigUrl = self.configUrl[::-1].replace(bareResourceName[::-1], self.newPrimaryKey[::-1], 1)[::-1]
                    #Check if the new key already exists in zookeeper
                    callback = configManager.zkClient.exists_async(updatedConfigUrl)
                    callback.rawlink(self.checkKeyFree)
                else:
                    if self.txnId:
                        self.zk_transactions[self.txnId].set_data(self.configUrl, bytes(self.config))
                        self.on_update_zk(None, self.txnId)
                    else:
                        callback = zkSetAsync(self.configUrl,
                                              bytes(self.config))
                        callback.rawlink(self.on_update_zk)
        else:
            self.write_err("Invalid configuration. Does not validate against the schema.")
            self.flush()
            self.finish()
            log.warn("xsd schema mismatch for user data:\n" + etree.tostring(userConfigs) + "\nschema: " + str(data))

    @log_close_webrequest_exception
    def checkKeyFree(self, response):
        doesExist = response.get()
        #If key already exists, don't do anything
        if doesExist:
            self.write_err("Error. The name " + self.newPrimaryKey + " already exists.")
            self.flush()
            self.finish()
        else:
            if self.txnId:
                self.zk_transactions[self.txnId].delete(self.configUrl)
                self.zk_transactions[self.txnId].delete(self.configUrl.replace("config", "config_schema", 1))
            else:
                configManager.zkClient.delete_async(self.configUrl)
                configManager.zkClient.delete_async(self.configUrl.replace("config", "config_schema", 1))
            #Modify the url so that it only contains the table name
            self.configUrl = self.configUrl[:-len(self.resourceName.split("/")[-1])-1]
            self.createSequenceNode(self.config, self.txnId)

    @log_close_webrequest_exception
    def on_update_zk(self, response, txnId=None):
        if txnId:
            self.write_success("Actions successfully added to transaction")
        else:
            response.get()
            self.write_success("Config successfully updated")
        self.flush()
        self.finish()

    #Delete a resource if allowed
    @tornado.web.asynchronous
    def delete(self, fullResourceName, fullNodeNameOrGlobal, nodeType, nodeId, appName, resourceName, lastResource, xmlStr, fullTxnId, txnId):
        if txnId:
            if txnId not in self.zk_transactions:
                self.write_err("Invalid transaction id")
                self.flush()
                self.finish()
                return
        self.fullTxnId = fullTxnId
        self.txnId = txnId
        if fullNodeNameOrGlobal == "/global_configs":
          #revert for global!!!
          #self.configUrl = "/epoch/global_confs" + self.request.path
          self.configUrl = "/epoch/version-" + configManager.parent.version + self.request.path
        else:
          self.configUrl = "/epoch/version-" + configManager.parent.version  + self.request.path
        self.configUrl = self.removeResourceTrails(self.configUrl)

        self.schemaConfigUrl = self.configUrl.replace("config", "config_schema", 1)
        self.flagUrl = self.configUrl.replace("config", "config_flags", 1)
        self.appName = appName
        # Check if deletable
        callback = zkGetAsync(self.flagUrl)
        callback.rawlink(self.handleIsDelete)

    @log_close_webrequest_exception
    def handleIsDelete(self, response):
        data, stat = response.get()
        if data:
            data = eval(data)
            if data["deleteFlag"] == True:
                if self.txnId:
                    self.zk_transactions[self.txnId].delete(self.configUrl)
                    self.zk_transactions[self.txnId].delete(self.schemaConfigUrl)
                    self.zk_transactions[self.txnId].delete(self.flagUrl)
                    self.sendDeleteConfig(None)
                else:
                    callback = configManager.zkClient.delete_async(self.configUrl)
                    callback.rawlink(self.sendDeleteConfig)
                    configManager.zkClient.delete_async(self.schemaConfigUrl)
                    configManager.zkClient.delete_async(self.flagUrl)
            else:
                self.write_err(self.configUrl + " is not allowed to be deleted")
                self.flush()
                self.finish()
        #...or that it is a node id. Delete the node id configs and routinginfo
        elif not self.appName:
            configManager.parent.scheduleThread(configManager.parent.zkThreadId, global_consts.MAX_EVENT_PRIO - 1, configManager.deleteConfig, self.configUrl)
            #configManager.zkClient.delete(self.configUrl, recursive=True)
            #configManager.zkClient.delete(self.schemaConfigUrl, recursive=True)
            configManager.zkClient.delete_async("/epoch/routinginfo/"+nodeId)
            self.write_success("Node successfully deleted")
            self.flush()
            self.finish()
        else:
            self.write_err(self.configUrl + " is not allowed to be deleted")
            self.flush()
            self.finish()

    def sendDeleteConfig(self, response):
        if self.txnId:
            self.write_success("Actions successfully added to transaction")
        else:
            self.write_success("Resource successfully deleted")
        self.flush()
        self.finish()

    @log_close_webrequest_exception
    def createSequenceNode(self, value, txnId):
        self.appId = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_name[self.appName].number
        tableUrl = self.configUrl
        if not tableUrl.endswith('/'):
            tableUrl += '/'
        configManager.createTableRow(tableUrl, value, self.appId, self.isLocal, asyncCallback=self.handleCreateSequenceNode, fullUrl=True, txnId=txnId, zk_transactions=self.zk_transactions)

    @log_close_webrequest_exception
    def handleCreateSequenceNode(self, response, txnId=None):
        if txnId:
            self.write_success("Actions added to transaction")
            self.flush()
            self.finish()
            return
        self.newConfigUrl = response.get()
        self.newConfigResource = self.newConfigUrl.split('/',RESOURCE_POSITION)[RESOURCE_POSITION]
        seqIndex = self.newConfigResource.rfind('/')
        self.seqNum = self.newConfigResource[seqIndex+1:]
        self.write_success("seqNum " + self.seqNum)
        self.flush()
        self.finish()

"""
ConfigSchemaHandler
Allows the user to see the configuration schemas taken from zookeeper.
These schemas show what values are allowed for each configuration.
"""
class ConfigSchemaHandler(WebRequestHandler):
    @tornado.web.asynchronous
    def get(self, fullNodeNameOrGlobal, nodeType, nodeId, appName, resourceName):
        #log.info("fullNodename: " + str(fullNodeNameOrGlobal) + "\nnodeType: " + str(nodeType) + "\nnodeId: " + str(nodeId) + "\nappName" + str(appName) + "\nresourceName: " + str(resourceName))
        if fullNodeNameOrGlobal == "global_configs":
          #revert for global!!!
          #self.resource = "/epoch/global_confs" + self.request.path
          self.resource = "/epoch/version-" + configManager.parent.version + self.request.path
        else:
          self.resource = "/epoch/version-" + configManager.parent.version + self.request.path
        # Send request to zookeeper to get config schema
        if not configManager.zkClient.connected:
          self.write_err("Not connected to zookeeper")
          self.flush()
          self.finish()
        else:
          try:
              callback = zkGetAsync(self.resource)
              callback.rawlink(self.on_get)
          except Exception, e:
              log.error("exception", exc_info=full_exc_info())
              self.write_err(e)
              self.flush()
              self.finish()

    @log_close_webrequest_exception
    def on_get(self, response):
        data, stat = response.get()
        try:
            json_data = eval(data)
            self.write_success(data)
        except:
            self.write_success(data)
        self.flush
        self.finish()

"""
ConfigFlagHandler
Allows the user to see the configuration flags taken from zookeeper.
These flags show the metadata for each configuration.
"""
class ConfigFlagsHandler(WebRequestHandler):
    @tornado.web.asynchronous
    def get(self, fullNodeNameOrGlobal, nodeType, nodeId, appName, resourceName):
        #log.info("fullNodename: " + str(fullNodeNameOrGlobal) + "\nnodeType: " + str(nodeType) + "\nnodeId: " + str(nodeId) + "\nappName" + str(appName) + "\nresourceName: " + str(resourceName))
        if fullNodeNameOrGlobal == "global_configs":
          #revert for global!!!
          #self.resource = "/epoch/global_confs" + self.request.path
          self.resource = "/epoch/version-" + configManager.parent.version + self.request.path
        else:
          self.resource = "/epoch/version-" + configManager.parent.version + self.request.path
          # Send request to zookeeper to get config flag
          if not configManager.zkClient.connected:
              self.write_err("Not connected to zookeeper")
              self.flush()
              self.finish()
          else:
              try:
                  callback = zkGetAsync(self.resource)
                  callback.rawlink(self.on_get)
              except Exception, e:
                  log.error("exception", exc_info=full_exc_info())
                  self.write_err(e)
                  self.flush()
                  self.finish()

    @log_close_webrequest_exception
    def on_get(self, response):
        data, stat = response.get()
        json_data = eval(data)
        self.flagsDict = {"flags":json_data}
        #Check if it's a table. If it is, get its children
        if json_data["isTable"] == True:
            #Get Children
            callback = configManager.zkClient.get_children_async(self.resource)
            callback.rawlink(self.getChildren)
        else:
            self.write_success(self.flagsDict)
            self.flush()
            self.finish()

    @log_close_webrequest_exception
    def getChildren(self, response):
        children = response.get()
        self.numChildren = len(children)
        self.flagsDict["children"] = {}
        if self.numChildren == 0:
            self.write_success(self.flagsDict)
            self.flush()
            self.finish()
        for child in children:
            childUrl = self.resource + "/" + child
            callback = zkGetAsync(childUrl)
            callback.rawlink( partial(self.getChild, child))

    @log_close_webrequest_exception
    def getChild(self, child, response):
        data, stat = response.get()
        json_data = eval(data)
        self.flagsDict["children"].update({child:json_data})
        self.numChildren -= 1
        if self.numChildren <= 0:
            self.write_success(self.flagsDict)
            self.flush
            self.finish()

class ConfigurationManager:
    def __init__(self):
        self.zkClient = None
        self.parent = None
        self.tables = set() #List of known tables
        self.watchers = {}  #{ resourceName : [watching app id] }
        self.configValues = [] #List of all config values owned by API server
        self.lc = None   #Looping call for sending keep alives to zookeeper

    def setConfiguration(self):
      pass

    def setZKClient(self, client):
        self.zkClient = client
        if self.lc:
            configManager.parent.reactor.callFromThread(self.lc.stop)
        self.lc = LoopingCall(self.sendKeepAlive)
        self.lc.start(ZK_KEEP_ALIVE_PERIOD, True)

    def setParent(self, parent):
        self.parent = parent

    def get_global_manager(self):
        return configManager

    def createTableRow(self, tableUrl, xmlData, destAppId, isLocal, asyncCallback=None, fullUrl=False, txnId=None, zk_transactions=None):
        primaryKey = ''
        match = re.search('(?<=config_primary_key>).+(?=</config_primary_key)', xmlData)
        appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[destAppId].name
        configPrefix = "config/{0}/" + appName + "/"
        configPrefix = BindUrlScope(configPrefix, isLocal)
        zkUrl = tableUrl
        if not fullUrl:
            zkUrl = configPrefix + tableUrl
        resourceName = tableUrl[:-1]
        if match:
            primaryKey = match.group(0)
        if not primaryKey:
            if not asyncCallback:
                newConfigUrl = self.zkClient.create(
                                    zkUrl,
                                    bytes(xmlData),
                                    makepath=True,
                                    sequence=True)
            else:
                if txnId:
                    zk_transactions[txnId].create(zkUrl, bytes(xmlData), sequence=True)
                    asyncCallback(None, txnId)
                else:
                    newConfigUrl = self.zkClient.create_async(
                                    zkUrl,
                                    bytes(xmlData),
                                    makepath=True,
                                    sequence=True)
                    newConfigUrl.rawlink(asyncCallback)
        else:
          try:
              if not asyncCallback:
                  newConfigUrl = self.zkClient.create(
                                    zkUrl+primaryKey,
                                    bytes(xmlData),
                                    makepath=True)
              else:
                  if txnId:
                    zk_transactions[txnId].create(zkUrl+primaryKey, bytes(xmlData))
                    asyncCallback(None, txnId)
                  else:
                      newConfigUrl = self.zkClient.create_async(
                                    zkUrl+primaryKey,
                                    bytes(xmlData),
                                    makepath=True)
                      newConfigUrl.rawlink(asyncCallback)
          except Exception,e:
              log.error("exception", exc_info=full_exc_info())
              newConfigUrl = zkUrl+primaryKey
              if not asyncCallback:
                  data, stat = zkGet(newConfigUrl,
                                                 watch=self.watchedUpdate)
            #Send the value if it differs from the process's current value
                  if xmlData != data:
                      self.sendConfigUpdate(data, stat, resourceName, destAppId)
        return newConfigUrl

    #Gives a resourcename and its data to zookeeper to store.
    #Also adds watches
    def addConfigResource(self, resourceName, resourceSchema,
                          currentValue, deleteFlag, srcAppId, appName, resource,
                          insertReq=False, isSequence=False, baseUrl=""):
        configPrefix = "config/{0}/" + appName + "/"
        configSchemaPrefix = "config_schema/{0}/" + appName + "/"
        configFlagsPrefix = "config_flags/{0}/" + appName + "/"
        configPrefix = self.ResolveResourceScope(configPrefix, resource)
        configSchemaPrefix = self.ResolveResourceScope(configSchemaPrefix, resource)
        configFlagsPrefix = self.ResolveResourceScope(configFlagsPrefix, resource)

        #If base url is provided, change the root of the url
        if baseUrl:
            configPrefix = configPrefix.replace("config", baseUrl, 1)

        #Check if proxy is connected to zookeeper
        if not self.zkClient.connected:
            return

        #Add resource to deletable list if delete flag is set
        if deleteFlag and not isSequence:
            self.parent.deletableRsrcs.add(configPrefix+resourceName)

        addPending = False
        deletePending = False
        flags = [] if "flags" not in resource else resource["flags"]
        if application_message_pb2.ApplicationMessage.ConfigResource.ADD_PENDING in flags:
            addPending = True
        if application_message_pb2.ApplicationMessage.ConfigResource.DELETE_PENDING in flags:
            deletePending = True

        if addPending:
            self.synchronousSetZKData(configPrefix+resourceName,
                                      currentValue)
            self.synchronousSetZKData(configSchemaPrefix+resourceName,
                                      resourceSchema)
            self.synchronousSetZKData(configFlagsPrefix+resourceName,
                                      {"deleteFlag":deleteFlag,
                                       "isTable": resourceName in self.tables})
            self.watchers[resourceName] = [srcAppId]
            zkGet(configPrefix+resourceName,
                              watch=self.watchedUpdate)
            params = { "appId": srcAppId,
                       "resourceName": resourceName}
            self.parent.createTool("AddPendingAckTool", params)
        elif deletePending:
            self.deleteConfig(configPrefix+resourceName)
            if not self.zkClient.exists(configPrefix+resourceName):
                params = { "appId": srcAppId,
                           "resourceName": resourceName}
                self.parent.createTool("DeletePendingAckTool", params)
        else:
            #Get latest value if zookeeper has the resource
            if not insertReq and self.zkClient.exists(configPrefix+resourceName):
                if resourceName in self.watchers:
                    if srcAppId not in self.watchers[resourceName]:
                        self.watchers[resourceName].append(srcAppId)
                data, stat = zkGet(configPrefix+resourceName,
                                               watch=self.watchedUpdate)
                #Send the value if it differs from the process's current value
                if currentValue != data:
                    self.sendConfigUpdate(data, stat, resourceName, srcAppId)
                # sync schema
                if not baseUrl:
                    schemaData, schemaStat = zkGet(configSchemaPrefix+resourceName)
                    if resourceSchema != schemaData:
                        self.synchronousSetZKData(configSchemaPrefix+resourceName, resourceSchema)
                    self.synchronousSetZKData(configFlagsPrefix+resourceName,
                                              {"deleteFlag":deleteFlag,
                                               "isTable": resourceName in self.tables})
            #Else create the resource in zookeeper, set the default value, and watch
            else:
                #If a sequence node, create it, and give the resource name to process
                if isSequence:
                    newConfigUrl = ""
                    if insertReq:
                        newConfigUrl = self.createTableRow(resourceName+'/', currentValue, srcAppId, resource["isLocal"])
                    #Remove the id
                    else:
                        index = resourceName.rfind('/')
                        #Table name with slash at end
                        tableUrl = configPrefix + resourceName[:index+1]
                        newConfigUrl = self.zkClient.create(
                                           tableUrl,
                                           bytes(currentValue),
                                           makepath=True,
                                           sequence=True)
                    #Add to deletion if delete flag is set
                    if deleteFlag:
                        self.parent.deletableRsrcs.add(newConfigUrl)
                    #Send the new resource name back to process
                    newConfigResource = newConfigUrl.split('/', RESOURCE_POSITION)[RESOURCE_POSITION]
                    seqIndex = newConfigResource.rfind('/')
                    seqNum = newConfigResource[seqIndex:]
                    #if insertReq is not set (the resource name has row name),
                    #delete it from process
                    if not insertReq and resourceName != newConfigResource:
                        self.sendDeleteConfigResources([resourceName], srcAppId)
                    #Send add config resource to process
                    params = { "appId": srcAppId,
                               "resources": [{"resourceName": newConfigResource,
                                              "currentValue": currentValue}]}
                    self.parent.createTool("AddConfigResourceTool", params)
                    if not baseUrl:
                        self.synchronousSetZKData(configSchemaPrefix+newConfigResource,
                                                  resourceSchema)
                        self.synchronousSetZKData(configFlagsPrefix+newConfigResource,
                                                  {"deleteFlag":deleteFlag,
                                                   "isTable": resourceName in self.tables})
                    self.watchers[newConfigResource] = [srcAppId]
                    zkGet(newConfigUrl,
                                      watch=self.watchedUpdate)
                #Not a sequence node
                else:
                    if len(bytes(currentValue)) > 1000000:
                        log.warn('saw a znode >1MB, skip')
                        return
                    if self.zkClient.exists(configPrefix+resourceName):
                        log.info(" Node Exists for " + str(configPrefix+resourceName))
                        self.zkClient.set(configPrefix+resourceName, bytes(currentValue))
                        params = { "appId": srcAppId,
                               "resources": [{"resourceName": resourceName,
                                              "currentValue": currentValue}]}
                        self.parent.createTool("AddConfigResourceTool", params)
                    else:
                        try:
                            self.zkClient.create(configPrefix+resourceName, bytes(currentValue), makepath=True)
                        except Exception as e:
                            log.error("Node already exists=" + str(configPrefix+resourceName))
                            pass

                    if not baseUrl:
                        self.synchronousSetZKData(configSchemaPrefix+resourceName,
                                                  resourceSchema)
                        self.synchronousSetZKData(configFlagsPrefix+resourceName,
                                                  {"deleteFlag":deleteFlag,
                                                   "isTable": resourceName in self.tables})
                    self.watchers[resourceName] = [srcAppId]
                    zkGet(configPrefix+resourceName,
                                      watch=self.watchedUpdate)

    #Send latest config value from zookeeper to requesting process
    def sendConfigUpdate(self, data, znodestat, resourceName, destAppId):
        params = {"value": data,
                  "resourceName": resourceName,
                  "appId" : destAppId}
        self.parent.createTool("ConfigUpdateTool", params)

    #Send deleted value from zookeeper to requesting process
    def sendDeleteConfigResources(self, resourceNames, destAppId):
        params = { "appId": destAppId,
                   "resourceNames": resourceNames }
        self.parent.createTool("DeleteConfigResourceTool", params)

    def deleteConfig(self, configUrl):
        try:
            self.zkClient.delete(configUrl, recursive=True)
        except Exception,e:
            log.error("exception", exc_info=full_exc_info())
        try:
            self.zkClient.delete(configUrl.replace('config','config_schema', 1), recursive=True)
        except Exception,e:
            log.error("exception", exc_info=full_exc_info())
        try:
            self.zkClient.delete(configUrl.replace('config','config_flags', 1), recursive=True)
        except Exception,e:
            log.error("exception", exc_info=full_exc_info())

    """
    When a process sends a table to create, check if it exists. If it does,
    sync the process with the zookeeper's values. Else, create the table.
    resource: first occurence table or row
    """
    def handleTableResource(self, tableName, tableSchema, tableRows, resource, destAppId):
        appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[destAppId].name

        configPrefix = "config/{0}/" + appName + "/"
        tableConfigUrl = "config/{0}/" + appName + "/" + tableName
        configPrefix = self.ResolveResourceScope(configPrefix, resource)
        tableConfigUrl = self.ResolveResourceScope(tableConfigUrl, resource)
        schemaPrefix = configPrefix.replace("config", "config_schema", 1)
        tableSchemaUrl = tableConfigUrl.replace("config", "config_schema", 1)
        flagsPrefix = configPrefix.replace("config", "config_flags", 1)
        tableFlagsUrl = tableConfigUrl.replace("config", "config_flags", 1)

        #If table exists, sync up the process's data with zookeeper's
        if self.zkClient.exists(tableConfigUrl):
            #Reset related urls in case they were not added
            self.synchronousSetZKData(tableSchemaUrl, tableSchema)
            self.synchronousSetZKData(tableFlagsUrl, {"deleteFlag":False,
                                                       "isTable":True})
            #Get the children from zookeeper
            childrenData = {}  #{child resource name: (child data, isSeen)}
            childrenList = self.zkClient.get_children(tableConfigUrl)
            for childName in childrenList:
                childUrl = tableConfigUrl + "/" + childName
                try:
                    data, stat = zkGet(childUrl,
                                           watch=self.watchedUpdate)
                    childrenData[tableName + "/" + childName] = [data, stat, False]
                except Exception as e:
                    log.warning("zkGet failed for url=" + str(tableName + "/" + childName) + " Reason: " + str(e), exc_info=full_exc_info())
            #Go through the table rows that the process has
            deletedResourceNames = []
            for row in tableRows:
                insertReq = False if "insertReq" not in row else row["insertReq"]
                resourceName = row["resourceName"]
                if "resourceSchema" in row:
                  resourceSchema = row["resourceSchema"]
                else:
                  resourceSchema = ""
                currentValue = '' if "currentValue" not in row else row["currentValue"]
                deleteFlag = False if "deleteFlag" not in row else row["deleteFlag"]

                addPending = False
                deletePending = False
                flags = [] if "flags" not in row else row["flags"]
                if application_message_pb2.ApplicationMessage.ConfigResource.ADD_PENDING in flags:
                    addPending = True
                if application_message_pb2.ApplicationMessage.ConfigResource.DELETE_PENDING in flags:
                    deletePending = True

                if addPending or deletePending:
                    if resourceName in childrenData: del childrenData[resourceName]
                    self.addConfigResource(resourceName, resourceSchema,
                                       currentValue,
                                       deleteFlag, destAppId, appName, row,
                                       insertReq=insertReq)
                else:
                    #If insertReq is set, add it to zookeeper
                    if insertReq:
                        self.addConfigResource(resourceName, resourceSchema,
                                           currentValue,
                                           deleteFlag, destAppId, appName, row,
                                           insertReq=insertReq)

                    #If row is not in zookeeper, delete it from process
                    elif row["resourceName"] not in childrenData:
                        deletedResourceNames.append( row["resourceName"] )
                    #If the row exists in zookeeper, check if process data is stale
                    else:
                        if deleteFlag:
                            self.parent.deletableRsrcs.add(configPrefix+row["resourceName"])
                        childData = childrenData[ row["resourceName"] ][0]
                        childStat = childrenData[ row["resourceName"] ][1]
                        childrenData[ row["resourceName"] ][2] = True
                        currData = row["currentValue"]
                        #If process data not the same as zookeeper's, update it
                        if currData != childData:
                            self.sendConfigUpdate(childData, childStat,
                                                  row["resourceName"],
                                                  destAppId=destAppId)
                        #Update the schema and flags urls for robustness
                        self.synchronousSetZKData(schemaPrefix+row["resourceName"], resourceSchema)
                        self.synchronousSetZKData(flagsPrefix+row["resourceName"],
                                                  {"deleteFlag":deleteFlag,
                                                   "isTable":False})
            if deletedResourceNames:
                self.sendDeleteConfigResources(deletedResourceNames, destAppId)
            #Go through the zookeeper children data and send new values to process
            newResources = []
            for resourceName, value in childrenData.iteritems():
                if value[2] == False:
                    newResources.append( {"resourceName": resourceName,
                                          "currentValue": value[0]} )
            if newResources:
                params = { "appId": destAppId,
                           "resources": newResources
                           }
                self.parent.createTool("AddConfigResourceTool", params)
        #If table does not exist, create it in zookeeper
        else:
            #Create the table
            #will have resourcename,and schema
            self.synchronousSetZKData(tableConfigUrl, "")
            self.synchronousSetZKData(tableSchemaUrl, tableSchema)
            self.synchronousSetZKData(tableFlagsUrl, {"deleteFlag":False,
                                                       "isTable":True})
            #Create the rows
            #will have name, schema, currentvalue, deleteflag
            for row in tableRows:
                #resource name
                resourceName = row["resourceName"]
                #resource schema
                resourceSchema = row["resourceSchema"]
                #current value
                currentValue = '' if "currentValue" not in row else row["currentValue"]
                #delete flag
                deleteFlag = False if "deleteFlag" not in row else row["deleteFlag"]
                insertReq = False if "insertReq" not in row else row["insertReq"]
                primaryKey = ''
                match = re.search('(?<=config_primary_key>).+(?=</config_primary_key)', currentValue)
                if match:
                    primaryKey = match.group(0)
                if primaryKey:
                    self.addConfigResource(resourceName, resourceSchema,
                                       currentValue,
                                       deleteFlag, destAppId, appName, row,
                                       insertReq=insertReq)
                else:
                    self.addConfigResource(resourceName, resourceSchema,
                                       currentValue,
                                       deleteFlag, destAppId, appName, row,
                                       insertReq=insertReq, isSequence=True)
        # track each table in ChildrenWatch only once
        if tableConfigUrl not in g_tables:
            ChildrenWatch(self.zkClient, tableConfigUrl, partial(self.handleChildrenWatch, tableConfigUrl))
            g_tables.add(tableConfigUrl)

    #Delete the resource and its schema
    def handleDeleteConfigResources(self, message):
        resources = message["applicationMessage"]["deleteConfigResources"]["resources"]
        srcAppId = message["messageAttributes"]["sourceAppId"]
        appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[srcAppId].name
        configPrefix = "config/{0}/" + appName + "/"
        configSchemaPrefix = "config_schema/{0}/" + appName + "/"
        configFlagsPrefix = "config_flags/{0}/" + appName + "/"
        for resource in resources:
            self.zkClient.delete(self.ResolveAndAppendResource(configPrefix, resource), recursive=True)
            self.zkClient.delete(self.ResolveAndAppendResource(configSchemaPrefix, resource), recursive=True)
            self.zkClient.delete(self.ResolveAndAppendResource(configFlagsPrefix, resource), recursive=True)

    #Update zookeeper if the value is validated against the schema
    def handleConfigUpdate(self, message):
        configUpdate = message["applicationMessage"]["configUpdate"]
        #resource name
        resourceName = configUpdate["resourceName"]
        value = configUpdate["value"]
        localFlag = configUpdate["localFlag"]
        #source app id
        srcAppId = message["messageAttributes"]["sourceAppId"]

        if not self.zkClient.connected:
            pass
        else:
            srcAppId = message["messageAttributes"]["sourceAppId"]
            appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[srcAppId].name


            configUrl = BindUrlScope("config/{0}/" + appName + "/" + resourceName, localFlag)
            schemaUrl = configUrl.replace("config", "config_schema", 1)
            if self.zkClient.exists(schemaUrl):
                data, stat = zkGet(schemaUrl)
                schema = etree.XMLSchema( etree.XML(data) )
                userConfigs = etree.parse(BytesIO(str(value)))
                try:
                    if len(bytes(value)) > 1000000:
                        log.warn('saw a znode >1MB, skip')
                        return
                    if schema.validate(userConfigs):
                        #Check if there is a config primary key. If there is,
                        #if it differs from the resource name, delete one and create new url
                        newPrimaryKey = ""
                        match = re.search('(?<=config_primary_key>).+(?=</config_primary_key)', str(value))
                        if match:
                            newPrimaryKey = match.group(0)
                        #If key is different
                        if newPrimaryKey and not resourceName.endswith(newPrimaryKey):
                            bareResourceName = resourceName.split("/")[-1]
                            tableName = resourceName.split("/")[0]
                            #url reverse replace
                            updatedConfigUrl = configUrl[::-1].replace(bareResourceName[::-1], newPrimaryKey[::-1], 1)[::-1]
                            #Check if the new key already exists in zookeeper
                            #callback = configManager.zkClient.exists_async(updatedConfigUrl)
                            #callback.rawlink(self.checkKeyFree)
                            zkSet(updatedConfigUrl, bytes(value))
                        else:
                            zkSet(configUrl, bytes(value))
                    else:
                      log.warn("xsd schema mismatch for app data:\n" + etree.tostring(userConfigs) + "\nschema: " + str(data))
                except Exception,e:
                    log.warning("Invalid configuration: " + value + "\nReason: " + str(e), exc_info=full_exc_info())
            else:
                log.warning("Schema does not exist for: " + resourceName)

            #configUrl = "http://localhost:"+str(self.parent.webPort)+"/config/node-" + self.parent.localNodeId + "/" + appName+ "/" + resourceName
            #self.http_client.fetch(configUrl, None, method='POST', body=value)

    def handleConfigSchemaUpdate(self, message):
        configSchemaUpdate = message["applicationMessage"]["configSchemaUpdate"]
        if "schemas" in configSchemaUpdate:
          schemas = configSchemaUpdate["schemas"]
        else:
          return
        for schema in schemas:
          resourceName = schema["resourceName"]
          resourceSchema = schema["resourceSchema"]
          localFlag = schema["localFlag"]
          srcAppId = message["messageAttributes"]["sourceAppId"]
          if not self.zkClient.connected:
            pass
          else:
            srcAppId = message["messageAttributes"]["sourceAppId"]
            appName = util_functions.getAppName(srcAppId)
            schemaUrl = BindUrlScope("config_schema/{0}/" + appName + "/" + resourceName, localFlag)
            if self.zkClient.exists(schemaUrl):
                callback = zkSet(schemaUrl, bytes(resourceSchema))
            else:
                self.zkClient.create(schemaUrl, bytes(resourceSchema), makepath=True)
    
    def createOrSetSingleMetadataRow(self, path ,value, response):
        doesExist = response.get()
        if doesExist:
            self.zkClient.set_async(path ,value)
        else:
            self.zkClient.create_async(path ,value , makepath=True)
            log.warning("Create metadata row for " + str(path))
    
    def addSingleMetadataRow(self, path ,value):
        callback =configManager.zkClient.exists_async(path)
        callback.rawlink(partial(self.createOrSetSingleMetadataRow,path ,value))


    def handleAddMetadata(self, message):
        resources = message["applicationMessage"]["addConfigResources"]["resources"]
        metadata = message["applicationMessage"]["addConfigResources"]["resources"][0]["currentValue"]
        data = json.loads(metadata)["metadataList"]
        log.info(" Received Metadata with number of rows =" + str(len(data)))
        for row in data:
            root = ET.Element('Tuple')
            key = ET.SubElement(root, 'config_primary_key')
            organization_id = ET.SubElement(root, 'ORGANIZATIONID')
            source = ET.SubElement(root, 'SOURCE')
            instance_to_metadata = ET.SubElement(root, 'INSTANCE_TO_METADATA')
            timestamp = ET.SubElement(root, 'TIMESTAMP')
            TTL = ET.SubElement(root, 'TTL')

            key.text= row["organization_id"] + "_" + row["source"]
            organization_id.text = row["organization_id"]
            source.text= row["source"]
            i2m = json.dumps((row.get("instance_to_metadata")))
            instance_to_metadata.text = i2m 
            timestamp.text =str(row["timestamp"])
            TTL.text = str(row.get("TTL" , "86400"))
            value = ET.tostring(root, encoding='utf8', method='xml')
            #TODO get these path in better way
            path = "/epoch/version-" + str(configManager.parent.version) + "/config/role-" + str(configManager.parent.role) + "/SCALANYTICS_ID/" + "WorkflowConfig/session-collector/source_metadata/" + str(row["organization_id"] + "_" + row["source"])
            self.addSingleMetadataRow(path ,value)
        # track each table in ChildrenWatch only once
        #TODO need to check o if this is required ??
        tableConfigUrl =  "/epoch/version-" + str(configManager.parent.version) + "/config/role-" + str(configManager.parent.role) + "/SCALANYTICS_ID/" + "WorkflowConfig/session-collector/source_metadata"
        if tableConfigUrl not in g_tables:
            ChildrenWatch(self.zkClient, tableConfigUrl, partial(self.handleChildrenWatch, tableConfigUrl))
            g_tables.add(tableConfigUrl)
        log.info(" Finished handleAddMetadata")



    def handleAddConfigResources(self, message):
        resources = message["applicationMessage"]["addConfigResources"]["resources"]
        #log.info("message received: " + str(resources))
        #source app id
        srcAppId = message["messageAttributes"]["sourceAppId"]
        #app name
        appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[srcAppId].name
        if appName == "API_RECEIVER_SERVICE_ID":
            self.handleAddMetadata(message)
            return
        #dictionary { tableName : (schema, [table rows as ConfigResource])}
        tableDict = {}
        tableName = ""
        for resource in resources:
            #print str( resource)
            resourceName = resource["resourceName"]
            resourceSchema = resource["resourceSchema"]
            currentValue = '' if "currentValue" not in resource else resource["currentValue"]
            deleteFlag = False if "deleteFlag" not in resource else resource["deleteFlag"]
            isTable = False if "isTable" not in resource else resource["isTable"]
            isRow = False if "isRow" not in resource else resource["isRow"]
            #If not table or row, add normally
            if not isTable and not isRow:
                self.addConfigResource(resourceName, resourceSchema,
                                       currentValue,
                                       deleteFlag, srcAppId, appName, resource)
            #If table, start collecting its rows
            elif isTable:
                tableName = resourceName
                tableDict[tableName] = (resourceSchema, [], resource)
                self.tables.add(tableName)
            #If it's a row, append
            elif isRow:
                if not tableName:
                    index = resourceName.rfind('/')
                    if index != -1:
                        tableName = resourceName[:index]
                    else:
                        tableName = resourceName
                    tableDict[tableName] = (resourceSchema, [resource], resource)
                else:
                    tableDict[tableName][1].append(resource)
        #Work with tables here
        for tableName, value in tableDict.iteritems():
            self.handleTableResource(tableName, value[0],
                                     value[1], value[2], srcAppId)

    #Send keep alives to zookeeper
    def sendKeepAlive(self):
        try:
            zkGetAsync("/epoch")
        except Exception as e:
            log.error(" Exception while processing sendKeepAlive : " + str(e))

    def GetUrl(self, uri, srcAppName, srcNodeId):
        name = uri["name"]
        type = uri["resourceType"]
        if "appId" not in uri:
          appName = srcAppName
        else:
          appName = util_functions.getAppName(uri["appId"])
        nodeId = srcNodeId if "nodeId" not in uri else uri["nodeId"]
        return "/epoch/version-" + self.parent.version + "/" + type + "/" + "node-" + nodeId + "/" + appName + "/" + name

    '''Retrieves data from zookeeper from the specified resource url and sends
       the results back on a callback function. May have optional watch callback
    '''
    def getZKData(self, resourceUrl, callback, watch=None):
        cb = zkGetAsync(resourceUrl, watch=watch)
        cb.rawlink(callback)

    '''Sets data in zookeeper from specified url and sends znodestat
       if successful
    '''
    def setZKData(self, resourceUrl, data, callback=None, **arg):
        cb = self.zkClient.create_async(resourceUrl, bytes(data), makepath=True, **arg)
        cb.rawlink(partial(self.handleSetZKData, resourceUrl, data, callback))

    def handleSetZKData(self, resourceUrl, data, callback, response):
        try:
            response.get()
        except:
            cb = zkSetAsync(resourceUrl,
                                         bytes(data))
            if callback:
                cb.rawlink(callback)

    def synchronousSetZKData(self, zkUrl, data, **arg):
        try:
            self.zkClient.create(zkUrl, bytes(data), makepath=True, **arg)
        except:
            zkSet(zkUrl, bytes(data))

    def synchronousSetZKDataWithVersion(self, resourceUrl, data, appId, isLocal, **arg):
        appName = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_number[appId].name
        configPrefix = "config/{0}/" + appName + "/"
        configPrefix = BindUrlScope(configPrefix, isLocal)
        zkUrl = configPrefix + resourceUrl
        try:
            self.zkClient.create(zkUrl, bytes(data), makepath=True, **arg)
        except:
            zkSet(zkUrl, bytes(data))

    def handleChildrenWatch(self, tableName, children):
        # Delete rows in the global table if they got deleted
        if tableName in g_tableChildren:
            rowsToDelete = []
            rows = g_tableChildren[tableName]
            for row in rows:
                if row not in children:
                    rowsToDelete.append(row)
            for row in rowsToDelete:
                deleteTableRow(tableName, row)
        if len(children) > 0:
            #get table schema
            cb = self.zkClient.get_async(tableName.replace("config", "config_schema", 1))
            cb.rawlink(partial(self.handleChildrenWatch1, children, tableName))

    def handleChildrenWatchSM(self, tableName, tableSchema, children):
        try:
            newResources = []
            newPathsforWatch = []
            appId = util_functions.getAppId("SCALANYTICS_ID")
            for child in children:
                try:
                    if tableName in g_tableChildren:
                        if child in g_tableChildren[tableName]:
                            continue
                    fullUrl = tableName+"/"+child
                    newPathsforWatch.append(fullUrl)
                    #TODO This can give exception as watch can return a already deleted resource 
                    data, stat =zkGet(fullUrl, watch=self.watchedUpdate)
                    newConfigResource = fullUrl.split('/',RESOURCE_POSITION)[RESOURCE_POSITION]
                    seqIndex = newConfigResource.rfind('/')
                    seqNum = newConfigResource[seqIndex+1:]
                    newResources.append( {"resourceName": newConfigResource ,"currentValue": data} )
                except Exception as e:
                    log.error("Exception in handleChildrenWatchSM for child " + str(child) + str(e))
                    pass
            if newResources:
                params = { "appId": appId, "resources": newResources }
                self.parent.createTool("AddConfigResourceTool", params)
            self.handleCreateSMSchemaAndPath(newPathsforWatch,tableSchema, appId)
        except Exception as e:
            log.error("Exception in handleChildrenWatchSM" + str(e))
    
    def handleCreateSMSchemaAndPath(self, newPathsforWatch, tableSchema , appId):
            for fullUrl in newPathsforWatch:
                try:
                    newConfigResource = fullUrl.split('/',RESOURCE_POSITION)[RESOURCE_POSITION]
                    seqIndex = newConfigResource.rfind('/')
                    seqNum = newConfigResource[seqIndex+1:]
                    cbS = configManager.zkClient.exists_async(fullUrl.replace("config", "config_schema", 1))
                    cbF = configManager.zkClient.exists_async(fullUrl.replace("config", "config_flags", 1))
                    cbS.rawlink(partial(self.handleCreateSMSchema, fullUrl,tableSchema, appId, seqNum))
                    cbF.rawlink(partial(self.handleCreateSMFlag, fullUrl))
                except Exception as e:
                   log.error("Exception in handleCreateSMSchemaAndPath for path" + str(fullUrl) + str(e))

    def handleCreateSMSchema(self, fullUrl, tableSchema , appId, seqNum, response):
        exist = response.get()
        if not exist:
            configManager.zkClient.create_async(
                       fullUrl.replace("config", "config_schema", 1),
                       bytes(tableSchema),
                       makepath=True)
            callback.rawlink(partial(self.updateWatchers, fullUrl, appId, seqNum))
    def handleCreateSMFlag(self, fullUrl, response):
        exist = response.get()
        if not exist:
            configManager.zkClient.create_async(
                fullUrl.replace("config", "config_flags", 1),
                bytes({"deleteFlag":True, "isTable":False}),
                makepath=True)
                

    def handleChildrenWatch1(self, children, tableName, response):
        try:
            tableSchema, _ = response.get()
            sourceMetadataTable = "/epoch/version-" + str(configManager.parent.version) + "/config/role-" + str(configManager.parent.role) + "/SCALANYTICS_ID/" + "WorkflowConfig/session-collector/source_metadata"
            if tableName == sourceMetadataTable:
                self.handleChildrenWatchSM(tableName, tableSchema, children)
                return
            for child in children:
                rowName = child
                if tableName in g_tableChildren:
                    if rowName in g_tableChildren[tableName]:
                        continue
                cb = self.zkClient.get_async(tableName+"/"+child)
                cb.rawlink(partial(self.handleChildrenWatch2, tableName+"/"+child, tableSchema))
        except Exception,e:
            log.error("Error in handleChildrenWatch1 " + str(e), exc_info=full_exc_info())

    def handleChildrenWatch2(self, url, tableSchema, response):
        try:
            urlData, stat = response.get()
            appName = url.split('/',RESOURCE_POSITION)[APP_POSITION]
            appId = util_functions.getAppId(appName)
            updateNewResource(url, urlData, appId, tableSchema)
        except Exception,e:
            log.error("Error in handleChildrenWatch2 " + str(e), exc_info=full_exc_info())

     #Watch function callback
    def watchedUpdate(self, event):
        log.debug("Watch received: " + str(event))
        if not self.parent.localNodeId:
            return
        resourceName = event.path.split('/', RESOURCE_POSITION)[RESOURCE_POSITION]
        appName = event.path.split('/',RESOURCE_POSITION)[APP_POSITION]
        if event.type == 'CHANGED':
            #Sends updated value and rewatch
            callback = zkGetAsync(event.path,
                                           watch=self.watchedUpdate)
            callback.rawlink(partial(self.watchEventChange, resourceName, appName))
        elif event.type == 'DELETED':
            if '/config/' in event.path:
                if resourceName in self.watchers:
                    appIds = self.watchers[resourceName]
                    for appId in appIds:
                        configManager.sendDeleteConfigResources([resourceName], appId)
                else:
                    appId = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_name[appName].number
                    self.watchers[resourceName] = [appId]
                    configManager.sendDeleteConfigResources([resourceName], appId)

    def watchEventChange(self, resourceName, appName, response):
        try:
            data, stat = response.get()
            if resourceName in self.watchers:
                appIds = self.watchers[resourceName]
                for appId in appIds:
                    configManager.sendConfigUpdate(data, stat, resourceName,
                                          appId)
            else:
                appId = message_attributes_pb2.EximiusMessageAttributes.DESCRIPTOR.enum_types_by_name['ApplicationId'].values_by_name[appName].number
                self.watchers[resourceName] = [appId]
                configManager.sendConfigUpdate(data, stat, resourceName, appId)
        except Exception,e:
            log.error("Error with processing watch change event", exc_info=full_exc_info());

    def ResolveAndAppendResource(self, url, resource):
      return self.ResolveResourceScope(url, resource) + resource["resourceName"]

    def ResolveResourceScope(self, url, resource):
      isLocal = resource["isLocal"]
      return BindUrlScope(url, isLocal)

def BindUrlScope(url, isLocal):
  if isLocal == False:
    role = configManager.parent.role
  else:
    role = ""
  if role != "":
    return "/epoch/version-" + configManager.parent.version + "/" + url.format("role-" + role)
  else:
    return "/epoch/version-" + configManager.parent.version + "/" + url.format("node-" + configManager.parent.localNodeId)


configManager = ConfigurationManager()

def config_manager_init(logger, parent, isApiServer = False):
  configManager.setParent(parent)
  global g_isApiServer
  g_isApiServer = isApiServer

  zookeeper_host = ZK_HOST + ":" + str(ZK_PORT)

  retryOptions = KazooRetry(max_tries=5, ignore_expire=True)
  zkClient = KazooClient(hosts=zookeeper_host,logger=logger,
                         connection_retry=retryOptions)
  zkClient.add_listener(kazoo_listener)
  configManager.setZKClient(zkClient)
  startZkClientLoop(zkClient)

def startZkClientLoop(zkClient):
  while not startZkClient(zkClient):
    from utils.monitor import running
    if not running:
      break
    pass

def startZkClient(zkClient):
  try:
      log.info( "starting zkClient")
      zkClient.start()
      log.info( "started zkClient")
      return True
  except:
      log.warning("startZkClient exception", exc_info=full_exc_info())
      return False
