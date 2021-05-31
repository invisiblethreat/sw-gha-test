File: FortinetPlugin.py
Search…

#!/usr/bin/env python2.7
# Line1
# Line2
# pylint: disable-msg=W0231
import sys
from MssPolicyMonitor.Plugin import FortinetApi
from MssPolicyMonitor.Plugin.PluginCommon import ( IServiceDevicePlugin,
                                                   IAggregationMgrPlugin,
                                                   IHAStatePlugin, IPolicyPlugin )
from MssPolicyMonitor.Lib import registerPlugin, FORTIMGR_PLUGIN
import ArTogglesPyAgent as featureToggle
if featureToggle.pyGetToggleState( 'MssFortinetPlugin' ):  # TODO remove for GA
   registerPlugin( FORTIMGR_PLUGIN, sys.modules[ __name__ ] )
def getAggMgrPluginObj( deviceConfig ):
   return FortiManagerPlugin( deviceConfig )
def getPluginObj( deviceConfig, aggMgrMemberId=None ):
   return FortiGatePlugin( deviceConfig, aggMgrMemberId )
####################################################################################
class FortiManagerPlugin( IAggregationMgrPlugin ):
   ''' MSS Service Policy Monitor Plugin for Fortinet FortiManager
   '''
   def __init__( self, deviceConfig ):
      self.deviceApi = FortinetApi.FortiManager( deviceConfig )
      self.deviceConfig = deviceConfig
   def getDeviceInfo( self ):
      ''' Return dict with at least these keys: 'ipAddr', 'name', 'model'
      '''
      return self.deviceApi.getDeviceInfo()
   def getAggMgrGroupMembers( self, groupName=None  ):
      ''' Return a list of firewalls accessible from this FortiManager
      '''
      if not groupName and 'group' in self.deviceConfig:
         groupName = self.deviceConfig[ 'group' ]
      return self.deviceApi.getGroupMembers( groupName )
   def closeApiConnection( self ):
      ''' Close any open connections to the service device
      '''
      return self.deviceApi.closeApiConnection()
####################################################################################
class FortiGatePlugin( IServiceDevicePlugin, IHAStatePlugin, IPolicyPlugin ):
   ''' MSS Service Policy Monitor Plugin for Fortinet FortiGate firewalls
   '''
   def __init__( self, deviceConfig, deviceName ):
      self.deviceApi = FortinetApi.FortiGate( deviceConfig, deviceName )
      self.deviceConfig = deviceConfig
   def getDeviceInfo( self ):
      ''' Return dict with at least these keys: 'ipAddr', 'name', 'model'
      '''
      return self.deviceApi.getDeviceInfo()
   def getHighAvailabilityState( self ):
      ''' Returns a ServiceDeviceHAState object with current
          High Availability State for the service device.
      '''
      return self.deviceApi.getHighAvailabilityState()
   def getPolicies( self, mssTags=None ):
      ''' Returns a list of ServiceDevicePolicy objects
      '''
      return self.deviceApi.getPolicies( mssTags=mssTags )
   def getInterfacesInfo( self, returnDict=False, resolveZoneNames=True ):
      ''' Returns a list of NetworkInterface objects
      '''
      return self.deviceApi.getInterfacesInfo( returnDict=returnDict )
   def getInterfaceNeighbors( self ):
      ''' Returns a dict of service device neighbor links
      '''
      return self.deviceApi.getInterfaceNeighbors()
   def getDeviceResources( self ):
      ''' Returns a dict with device resource info
      '''
      return self.deviceApi.getDeviceResources()
   def closeApiConnection( self ):
      ''' Close any open connections to the service device
      '''
      return self.deviceApi.closeApiConnection()
#-----------------------------------------------------------------------------------
# tests
if __name__ == "__main__":
   deviceDict = {
      'ipAddress': 'bizdev-fortimgr', 'username': 'admin', 'password': 'company',
      'protocol': 'https', 'protocolPortNum': 443, 'method': 'tls',
      'verifyCertificate': False, 'timeout': 15, 'retries': 1,
      'exceptionMode': 'bypass', 'group': 'mssGroup',
      'adminDomain': 'root', 'virtualDomain': 'L2_Firewall',
      'interfaceMap': {
         'port29': {
            'switchIntf': 'Ethernet39', 'switchChassisId': '001c.737e.2811' },
         'port30' : {
            'switchIntf' : 'Ethernet40', 'switchChassisId' : '001c.737e.2811' },
         'port31' : {
            'switchIntf' : 'Ethernet41', 'switchChassisId' : '001c.737e.2811' },
         'port32' : {
            'switchIntf' : 'Ethernet42', 'switchChassisId' : '001c.737e.2811' },
         'port17': {
            'switchIntf': 'Port-Channel70', 'switchChassisId': '001c.737e.2811' },
         'port18': {
            'switchIntf': 'Port-Channel70', 'switchChassisId': '001c.737e.2811' },
         'port19': {
            'switchIntf': 'Port-Channel75', 'switchChassisId': '001c.737e.2811' },
         'port20': {
            'switchIntf': 'Port-Channel75', 'switchChassisId': '001c.737e.2811' },
      } }
   print '\nTEST FORTIMANAGER API CALLS'
   fmgr = getAggMgrPluginObj( deviceDict )
   info = fmgr.getDeviceInfo()
   print 'FortiManager DeviceInfo:', info, '\n'
   aggMembers = fmgr.getAggMgrGroupMembers( 'mssGroup' )
   print 'FortiManager AggMgrGroupMembers:', aggMembers
   firewall = aggMembers[ 0 ]
   fmgr.closeApiConnection()
   print '\nTEST FORTIGATE API CALLS for:', firewall
   fw = getPluginObj( deviceDict, firewall )
   info = fw.getDeviceInfo()
   print 'FortiGate DeviceInfo:', info, '\n'
   ha = fw.getHighAvailabilityState()
   print '\n' +'HAState:', ha, 'isHaPassiveOrSecondary:', ha.isHaPassiveOrSecondary()
   r = fw.getDeviceResources()
   print 'Resources:\n', r[ 'resourceInfo' ]
   intfs = fw.getInterfacesInfo()
   print 'Interfaces:'
   for intf in intfs:
      print intf
   nbors = fw.getInterfaceNeighbors()
   print '\nLLDP_Neighbors:', nbors
   pols = fw.getPolicies( mssTags=[ 'Company_MSS', 'mss1', 'mss2' ] )
   print '\nPolicies:'
   for p in pols:
      print p, '\n'
   fw.closeApiConnection()