/* Line1
Line2 */

/* global $, window */
'use strict';

var app = window.__tapagg__.app;
var parameters = window.__tapagg__.parameters;
var angular = window.__tapagg__.angular;

// Flags

// Require a non-empty enable password
var SHOULD_REQUIRE_ENABLE_PW = parameters.requireEnablePw;
var MOCK_ENABLE_PW = parameters.mockEnablePw;
var MOCK_ENABLE_PW_RETRIES_MIN = parameters.mockEnablePwRetriesMin;

// Autopopulate the display. Disable for tests.
var CREATE_INITIAL_GROUPS = parameters.createInitialGroups;


app.run( [ "$httpBackend", "$cookies", "$log", function( $httpBackend, $cookies, $log ) {

   // State
   var tapAggEnabled = true;
   var queueLengthEnabled = false;
   var currInterface = "";
   var currAccessList= null;
   var currClassMap = null;
   var currPolicyMap = null;
   var currPolicyMapClassMap = null;
   var nConfigSaves = 0; // every other save, generate an error
   var removeAccessList = function( accessList, aclListName ) {
      $.each( accessList.aclList, function( index, aclInfo ){
         if( aclInfo.name == aclListName ) {
            accessList.aclList.splice( index, 1 );
            return false;
         }
      } );
   };
   var enablePwTries = 0;

   // Configure the mock HTTP back-end to replace its reference
   // to angular.copy with this work-around. This improves copy
   // performance by 3+ orders of magnitude.
   $httpBackend.replaceCopyFunc( function ( src, dst ) {
      if ( dst || !angular.isObject( src ) || angular.isArray( src ) ) {
         return angular.copy( src, dst );
      }
      return $.extend( true, {}, src );
   } );

   $httpBackend.whenGET(/.*/).passThrough();

   $httpBackend.whenPOST( '/login' ).respond( function( method, url, data, headers ) {
      var parsedData = JSON.parse( data );
      $log.debug( "mockApp /login data=" + data + " headers=" + JSON.stringify( headers ) + " session cookie=" + $cookies.Session );
      if ( parameters.mockUsername ) {
         if ( ! $cookies.Session ) {
            if ( parsedData.username != parameters.mockUsername ) {
               $log.debug( "mockApp /login username mismatch" );
               return [ 401, {} ];
            } else if ( parameters.mockPassword && parsedData.password != parameters.mockPassword ) {
               $log.debug( "mockApp /login password mismatch" );
               return [ 401, {} ];
            } else {
               $cookies.Session = "1234567";
               $log.debug( "mockApp /login set session cookie to " + $cookies.Session  );
            }
         } else {
            $log.debug( "mockApp /login received session cookie " + $cookies.Session );
         }
      }
      return [ 200, {} ];
   } );

   $httpBackend.whenPOST( '/logout' ).respond( function( method, url, data, headers ) {
      $log.debug( "mockApp /logout headers=" + JSON.stringify( headers ) + " session cookie=" + $cookies.Session );
      $cookies.Session = "";
      return [ 200, {} ];
   } );

   $httpBackend.whenPOST( '/command-api' ).respond( function( method, url, data ) {
      var parsedData = JSON.parse( data );
      var result = [];
      var matches;
      var toolPort;
      var toolPorts;
      var group;
      var groups;
      var intfs;
      var name;
      var j;

      // Reset these on each request (commands sent across requests don't retain context, which is
      // fine for this "mock" use case)
      currAccessList= null;
      currClassMap = null;
      currPolicyMap = null;
      currPolicyMapClassMap = null;

      for( var i=0; i<parsedData.params.cmds.length; i++ ) {
         var cmd = parsedData.params.cmds[ i ];

         // Check for editConfig commands
         if( parsedData.method === 'editConfig' ) {
            if( parsedData.params.testOption === 'testOnly' ) {
               if( cmd.match( 'switchport tap truncation' ) ) {
                  if( !parameters.tapTruncationSupported ) {
                     // Just return an error to indicate the command is not supported
                     return [ 200, { "jsonrpc": parsedData.jsonrpc, "id": parsedData.id,  "error": { 
                        code: 1002,
                        message: "CLI command 1 of 1 '" + cmd + "' failed: invalid command",
                        data: [ { "errors": [ "not supported on this hardware platform (at token 999: 'sometoken')" ] } ],
                     } } ];
                  }
               }

               // All other commands are assumed to be valid
               result.push( {} );
               continue;
            }
         }
            
         if( typeof cmd == 'string' ) cmd = cmd.trim();
         if( typeof cmd === 'object' && cmd.cmd === 'enable' ) {
            // Process complex command requests first.
            enablePwTries += 1;
            if( SHOULD_REQUIRE_ENABLE_PW && cmd.input === '' ||
                MOCK_ENABLE_PW && cmd.input != MOCK_ENABLE_PW ||
                MOCK_ENABLE_PW_RETRIES_MIN && enablePwTries < MOCK_ENABLE_PW_RETRIES_MIN + 1 ) {
               return [
                  200,
                  {
                     "jsonrpc": parsedData.jsonrpc,
                     "id": parsedData.id,
                     "error": {
                        "data": [{ "errors": ["","Cannot authenticate unknown uid 10095"] }],
                        "message":
                           "CLI command 1 of 1 'enable' failed: permission to run command denied",
                        "code": 1005
                     }
                  }
               ];
            } else {
               result.push( {} );
            }
         } else if( cmd == "enable" || cmd == "configure" || cmd == "tap aggregation" ) {
            result.push( {} );
         } else if( cmd == "show version" ) {
            result.push( versionResponse );
         } else if( cmd == "show hostname" ) {
            result.push( { hostname: 'so123', fqdn: 'so123.companynetworks.com' } );
         } else if( cmd == "show running-config" ) {
            result.push( runningConfigResponse );
         } else if( cmd == "show running-config diffs" ) {
            result.push( runningConfigDiffResponse );
         } else if( cmd == "show interfaces" ) {
            $.each( allIntfResponse.interfaces, function( intf, intfObj ) {
               generateIntfCounters( intfObj.interfaceCounters, intfObj.bandwidth );
            });
            result.push( allIntfResponse );
         } else if( cmd == "show interfaces status" ) {
            result.push( allIntfStatusResponse );
         } else if( cmd == "show interfaces counters" ) {
            $.each( allIntfCountersResponse.interfaces, function( intf, intfObj ) {
               generateIntfCounters( intfObj, 10000000000 );
            });
            result.push( allIntfCountersResponse );
         } else if( cmd == "show interfaces tool detail" ) {
            result.push( intfToolResponse );
         } else if( cmd == "show interfaces tap detail" ) {
            result.push( intfTapDetailResponse );
         } else if( cmd == "show interfaces transceiver" ) {
            result.push( interfacesTransceiverResponse );
         } else if( cmd.match( "show interfaces [0-9A-Za-z-\/]+$" ) ) {
            // Get a single instance of an interfaces
            var intfName = cmd.match( /[0-9A-Za-z-\/]+$/g )[ 0 ];
            var intfResult = { "interfaces": {} };
            intfResult.interfaces[ intfName ] = allIntfResponse.interfaces[ intfName ];
            result.push( intfResult );
         } else if( cmd == "mode exclusive" ) {
            tapAggEnabled = true;
            result.push( {} );
         } else if( cmd == "no mode exclusive" ) {
            tapAggEnabled = false;
            result.push( {} );
         } else if( cmd == "show tap aggregation groups detail" ) {
            if( !tapAggEnabled ) {
               result.push( {"detail": true, "groups": {}, "errors": [ "Tap-aggregation is not enabled" ] } );
            } else {
               result.push( tapAggGroupDetailResponse );
            }
         } else if( cmd.match( "show logging threshold errors .*" ) ) {
            result.push( syslogErrorMessages );
         } else if( cmd.match( "show logging .*" ) ) {
            result.push( syslogMessages );
         } else if( cmd.match( "^interface .*" ) ) {
            currInterface = cmd.match( /[0-9A-Za-z-\/]+$/g )[ 0 ];
            result.push( {} );
         } else if( cmd === "shutdown" ) {
            allIntfResponse.interfaces[ currInterface ].interfaceStatus = "disabled";
            allIntfStatusResponse.interfaceStatuses[ currInterface ].linkStatus = "disabled";
            result.push( {} );
         } else if( cmd === "no shutdown" ) {
            allIntfResponse.interfaces[ currInterface ].interfaceStatus = "connected";
            allIntfStatusResponse.interfaceStatuses[ currInterface ].linkStatus = "connected";
            result.push( {} );
         } else if( cmd.match( "description .*" ) ) {
            var description = cmd.match( /^description (.*)$/ );
            if (description.length > 1) {
               description = description[ 1 ];
               allIntfResponse.interfaces[ currInterface ].description = description;
               allIntfStatusResponse.interfaceStatuses[ currInterface ].description = description;
            }
            result.push( {} );
         } else if( cmd.match( "no description" ) ) {
            allIntfResponse.interfaces[ currInterface ].description = '';
            allIntfStatusResponse.interfaceStatuses[ currInterface ].description = '';
            result.push( {} );
         } else if( cmd.match( "show ip access-lists.*" ) ){
            result.push( ipAcls );
         } else if( cmd.match( "show ipv6 access-lists.*" ) ){
            result.push( ipv6Acls );
         } else if( cmd.match( "show mac access-lists.*" ) ){
            result.push( macAcls );
         } else if( cmd.match( "no ip access-list .*" ) ) {
            removeAccessList( ipAcls, cmd.match( /\w+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "no ipv6 access-list .*" ) ) {
            removeAccessList( ipv6Acls, cmd.match( /\w+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "no mac access-list .*" ) ) {
            removeAccessList( macAcls, cmd.match( /\w+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "service-policy type tapagg input .*" ) ){
            name = cmd.match( /\w+$/g )[ 0 ];
            unsetTapIntfPolicyMap( currInterface );
            setTapIntfPolicyMap( currInterface, name );
            result.push( {} );
         } else if( cmd.match( "no service-policy type tapagg input" ) ){
            unsetTapIntfPolicyMap( currInterface );
            result.push( {} );
         } else if( cmd.match( "show class-map type tapagg" ) ){
            result.push( tapAggClassMaps );
         } else if( cmd.match( "show policy-map type tapagg" ) ){
            result.push( tapAggPolicyMaps );
         } else if( cmd.match( "no class-map type tapagg match-any .*" ) ) {
            removeClassMap( cmd.match( /\w+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "no policy-map type tapagg .*" ) ) {
            removePolicyMap( cmd.match( /\w+$/g )[ 0 ] );
            result.push( {} );
         } else if ( cmd.match( "class-map type tapagg match-any .*" ) ) {
            name = cmd.match( /\w+$/g )[ 0 ];
            currClassMap = tapAggClassMaps.classMaps[ name ];
            if( !currClassMap ) {
               currClassMap = createClassMap( name, {} );
               currClassMap.name = name;
            }
            result.push( {} );
         } else if ( cmd.match( "policy-map type tapagg .*" ) ) {
            name = cmd.match( /\w+$/g )[ 0 ];
            currPolicyMap = tapAggPolicyMaps.policyMaps[ name ];
            if( !currPolicyMap ) {
               currPolicyMap = createPolicyMap( name, true );
            }
            result.push( {} );
         } else if ( cmd.match( /^(\d+)? ?class (\w+)$/ ) ) {
            match = cmd.match( /^(\d+)? ?class (\w+)$/ );
            // Ensure that we are in policy map config mode already
            if( !currPolicyMap ) {
               result.push( {} );
               continue;
            }

            // Enter class config
            currPolicyMapClassMap = getOrCreateClassMapInPolicyMap( currPolicyMap, match[1], match[2] );
            result.push( {} );
         } else if ( cmd.match( /^set aggregation-group group ([\w+ ]+)$/ ) ) {
            // Ensure that we are in policy map config mode and in a class map submode
            if( !currPolicyMap || !currPolicyMapClassMap ) {
               result.push( {} );
               continue;
            }

            // Get the list of groups
            groups = cmd.match( /^set aggregation-group group ([\w+ ]+)$/ )[1].split(" group ");
            setAggregationGroupsForClassMapInPolicyMap( currPolicyMapClassMap, groups );
            result.push( {} );
         } else if ( cmd.match( /^set interface ((?:(?:\w|-|\/)+,?)+(?:(?:\w|-|\/)+))$/ ) ) {
            // Ensure that we are in policy map config mode and in a class map submode
            if( !currPolicyMap || !currPolicyMapClassMap ) {
               result.push( {} );
               continue;
            }

            // Get the list of tool port interfaces (either port channels or ethernet)
            intfs = cmd.match( /((?:(?:\w|-|\/)+,?)+(?:(?:\w|-|\/)+))$/ )[1].split(",");
            setToolPortIntfsForClassMapInPolicyMap( currPolicyMapClassMap, intfs );
            result.push( {} );
         } else if ( cmd.match( /^set id-tag (\d+)$/ ) ) {
            // Ensure that we are in policy map config mode and in a class map submode
            if( !currPolicyMap || !currPolicyMapClassMap ) {
               result.push( {} );
               continue;
            }

            // Get the list of tool port interfaces (either port channels or ethernet)
            var vlanId = cmd.match( /(\d+)$/ )[1];
            setVlanIdForClassMapInPolicyMap( currPolicyMapClassMap, vlanId );
            result.push( {} );
         } else if ( cmd.match( /^(no )?(\d+ )?match (ip|ipv6|mac) access\-group (\w+)$/ ) && currClassMap ){
            matches = cmd.match( /^(no )?(\d+ )?match (ip|ipv6|mac) access\-group (\w+)$/ );
            if( matches[ 1 ] ) {
               // This is a "no" entry and needs to be removed
               $.each( currClassMap.match.matchIpAccessGroup.acl, function( index, rule ) {
                  if( rule.sequenceNumber == matches[ 2 ] ) {
                     currClassMap.match.matchIpAccessGroup.acl.splice( index, 1 );
                     return false;
                  }
               } );
            } else {
               addAclToClassMap( currClassMap.name, matches[ 2 ], matches[ 3 ], matches[ 4 ] );
            }
            
            result.push( {} );
         } else if( cmd.match( /^(ip|ipv6|mac) access-list( standard)? (.*)$/ ) ) {
            currAccessList = null;
            matches =  cmd.match( /^(ip|ipv6|mac) access-list( standard)? (.*)$/ );
            var aclType = matches[ 1 ];
            var aclStandard = matches[ 2 ] ? true : false;
            var aclName = matches[ 3 ];
            
            var aclList = null;
            if( aclType == "ip" ) {
               aclList = ipAcls;
               aclType = "Ip4Acl";
            } else if( aclType == "ipv6" ) {
               aclList = ipv6Acls;
               aclType = "Ip6Acl";
            } else if( aclType == "mac" ) {
               aclList = macAcls;
               aclType = "MacAcl";
            }
            
            $.each( aclList.aclList, function( index, aclInfo ) {
               if( aclInfo.name == aclName ) {
                  currAccessList = aclInfo;
               }
            } );
            
            if( !currAccessList ) {
               currAccessList = { name: aclName, 
                     standard: aclStandard ? true : false, 
                     readonly: false, 
                     type: aclType, sequence: [ ] };
               aclList.aclList.push( currAccessList );
            }
            
            result.push( {} );
         } else if ( cmd.match( /^(?:(no) )?(\d+)(:? (.*))?$/ ) && currAccessList ){
            matches = cmd.match( /^(?:(no) )?(\d+)(:? (.*))?$/ );
            if( matches[ 1 ] ) {
               $.each( currAccessList.sequence, function( index, aclRule ) {
                  if( aclRule.sequenceNumber == matches[ 2 ] ) {
                     currAccessList.sequence.splice( index, 1 );
                     return false;
                  }
               } );
            } else {
               currAccessList.sequence.push( { sequenceNumber: matches[ 2 ], text: matches[ 4 ] } );
            }
            
            result.push( {} );
         } else if( cmd == "exit" ){
            // Some contexts are nested, so check in the right order and only exit one mode
            if( currPolicyMapClassMap ) {
               currPolicyMapClassMap = undefined;
            } else if( currPolicyMap ) {
               currPolicyMap = undefined;
            } else if( currClassMap ) {
               currClassMap = undefined;
            } else if( currAccessList ) {
               currAccessList = undefined;
            }
            result.push( {} );
         } else if( cmd == "queue-monitor length" ) {
            queueLengthEnabled = true;
            result.push( {} );
         } else if( cmd == "no queue-monitor length" ) {
            queueLengthEnabled = false;
            result.push( {} );
         } else if( cmd == "show queue-monitor length limit 1000 samples drops" ||
                    cmd.match( "show queue-monitor length limit [0-9]* seconds drops" ) ) {
            if( !parameters.lanzSupported ) {
               return [ 200, { "jsonrpc": parsedData.jsonrpc, "id": parsedData.id,  "error": { 
                  code: 1002,
                  message: "CLI command 1 of 1 'show queue-monitor length limit 1000 samples drops' failed: invalid command",
                  data: [ { "errors": [ "not supported on this hardware platform (at token 6: 'drops')" ] } ],
               } } ];
            } else if( queueLengthEnabled ) {
               result.push( queueLengthEnabledResponse );
            } else {
               result.push( queueLengthDisabledResponse );
            }
         } else if( cmd == "show queue-monitor length csv" ) {
            if( queueLengthEnabled ) {
               result.push( queueLengthEnabledResponseCsv );
            } else {
               result.push( queueLengthDisabledResponseCsv );
            }
         } else if( cmd == "no switchport tap truncation" ){
            intfTapDetailResponse.tapProperties[ currInterface ].truncationSize = 0;
            result.push( {} );
         } else if( cmd.match( "switchport tap truncation .*" ) ) {
            intfTapDetailResponse.tapProperties[ currInterface ].truncationSize = parseInt(
               cmd.match( /[0-9]+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd == "no switchport tool truncation" ){
            intfToolResponse.toolProperties[ currInterface ].details.truncationSize = 0;
            result.push( {} );
         } else if( cmd.match( "switchport tool truncation .*" ) ) {
            intfToolResponse.toolProperties[ currInterface ].details.truncationSize = parseInt(
               cmd.match( /[0-9]+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "switchport tap native vlan .*" ) ) {
            intfTapDetailResponse.tapProperties[ currInterface ].nativeVlan = parseInt(
               cmd.match( /[0-9]+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "switchport tap identity .*" ) ) {
            intfTapDetailResponse.tapProperties[ currInterface ].portIdentity = parseInt(
               cmd.match( /[0-9]+$/g )[ 0 ] );
            result.push( {} );
         } else if( cmd.match( "switchport tap allowed vlan .*" ) ) {
            intfTapDetailResponse.tapProperties[ currInterface ].allowedVlans = cmd.match( /[A-Za-z0-9,-]+$/g )[ 0 ];
            result.push( {} );
         } else if( cmd.match( "switchport tool allowed vlan .*" ) ) {
            intfToolResponse.toolProperties[ currInterface ].allowedVlans = cmd.match( /[A-Za-z0-9,-]+$/g )[ 0 ];
            result.push( {} );
         } else if( cmd == "switchport mode tap" ){
            
            intfTapDetailResponse.tapProperties[ currInterface ] = {
                  "allowedVlans": "All",
                  "nativeVlan": 1,
                  "details": {
                     "defaultGroup": "---",
                     "aclsAppliedPerType": {},
                     "groups": generateToolGroups(),
                     "toolPorts": generateToolPorts()
                  },
                  "truncationSize": 0,
                  "portIdentity": 1,
                  "linkStatus": "tap",
                  "configuredMode": "tap"
               };
            result.push( {} );
         } else if( cmd == "switchport mode tool" ) {
            intfToolResponse.toolProperties[ currInterface ] = {
                  "allowedVlans": "All",
                  "timestampMode": "None",
                  "identificationTag": "Off",
                  "linkStatus": "tool",
                  "configuredMode": "tool",
                  "details": {
                     "truncationSize": 0,
                     "aclsAppliedPerType" : {}
                  }
               };
            result.push( {} );
         } else if( cmd.match( "switchport tool identity .*" ) ) {
            intfToolResponse.toolProperties[ currInterface ].identificationTag = cmd.match( /[A-Za-z0-9,-]+$/g )[ 0 ];
            result.push( {} );
         } else if( cmd.match( "no switchport tool identity" ) ) {
            intfToolResponse.toolProperties[ currInterface ].identificationTag = "Off";
            result.push( {} );
         } else if( cmd.match( "mac timestamp .*" ) ) {
            intfToolResponse.toolProperties[ currInterface ].timestampMode = cmd.match( /[A-Za-z0-9,-]+$/g )[ 0 ];
            result.push( {} );
         } else if( cmd == "no mac timestamp" ) {
            intfToolResponse.toolProperties[ currInterface ].timestampMode = "None";
            result.push( {} );
         } else if( cmd.match( /^(no )?(ip|ipv6|mac) access-group (?:standard )?(\w*)? ?(in|out)$/ ) ) {
            var match = cmd.match( /^(no )?(ip|ipv6|mac) access-group (?:standard )?(\w*)? ?(in|out)$/ );
            var properties = null;
            
            if( match[ 4 ] == "in" ) {
               properties = intfTapDetailResponse.tapProperties[ currInterface ];
            } else if( match[ 4 ] == "out" ) {
               properties = intfToolResponse.toolProperties[ currInterface ];
            }
            
            if( match[ 1 ] ) {
               delete properties.details.aclsAppliedPerType[ match[ 2 ] ];
            } else {
               properties.details.aclsAppliedPerType[ match[ 2 ] ] = { aclsApplied: [ match[ 3 ] ] };
            }
            result.push( {} );
         } else if( cmd == "copy running-config startup-config" ) {
            nConfigSaves += 1;
            if( nConfigSaves % 2 === 0 ){ 
               return [ 200, { "jsonrpc": parsedData.jsonrpc, "id": parsedData.id,  "error": { 
                  code: 1000,
                  message: "Error executing command 2: 'copy running-config startup-config'",
                  data: [ { "errors": [ "Authorization denied for command" ] } ],
               } } ];
            }
         } else if( cmd.match( "switchport tool group add .*" ) ) {
            group = cmd.match( /[A-Za-z0-9]+$/g )[ 0 ];
            if ( !( group in tapAggGroupDetailResponse.groups ) ) {
               tapAggGroupDetailResponse.groups[ group ] = { "toolPortStatuses": {}, "tapPortStatuses": {} };
            }
            tapAggGroupDetailResponse.groups[ group ].toolPortStatuses[ currInterface ] = { "statuses": [ "Active" ] };
            result.push( {} );
         } else if( cmd.match( "switchport tool group remove .*" ) ) {
            group = cmd.match( /[A-Za-z0-9]+$/g )[ 0 ];
            delete tapAggGroupDetailResponse.groups[ group ].toolPortStatuses[ currInterface ];
            result.push( {} );
         } else if( cmd == "default switchport tool group" ) {
            $.each( tapAggGroupDetailResponse.groups, function( groupName, group ) {
               if( currInterface in group.toolPortStatuses ) {
                  delete group.toolPortStatuses[ currInterface ];
               }
            } );
            
            if( currInterface in intfToolResponse.toolProperties ) {
               delete intfToolResponse.toolProperties[ currInterface ];
            }
            result.push( {} );
         } else if( cmd.match( "no switchport tap default group" ) ) {
            $.each( tapAggGroupDetailResponse.groups, function( groupName, group ) {
               if( currInterface in group.tapPortStatuses ) {
                  delete group.tapPortStatuses[ currInterface ];
               }
            } );
            result.push( {} );
         } else if( cmd.match( "^switchport tap default group .*" ) ) {
            groups = cmd.match( /^switchport tap default group (.*)/ );
            groups = groups[1];
            groups = groups.split(" group ");
            $.each( groups, function( index, groupName ) {
               if ( !( groupName in tapAggGroupDetailResponse.groups ) ) {
                  tapAggGroupDetailResponse.groups[ groupName ] = { "toolPortStatuses": {}, "tapPortStatuses": {} };
               }

               tapAggGroupDetailResponse.groups[ groupName ].tapPortStatuses[ currInterface ] = 
                    { "statuses": [ "Active" ] };
            } );
            result.push( {} );
         } else if( cmd.match( "no switchport tap default interface" ) ) {
            intfTapDetailResponse.tapProperties[ currInterface ].details.toolPorts = [];
            result.push( {} );
         } else if( cmd.match( "^switchport tap default interface .*" ) ) {
            toolPorts = cmd.match( /((?:(?:\w|-|\/)+,?)+(?:(?:\w|-|\/)+))$/g )[ 0 ];
            toolPorts = toolPorts.split(",");
            // Remove all other interfaces so we can replace the list with the new one
            $.each( toolPorts, function( index, toolPort ) {
               if( !( toolPort in intfTapDetailResponse.tapProperties[ currInterface ].details.toolPorts ) ) {
                  intfTapDetailResponse.tapProperties[ currInterface ].details.toolPorts.push( toolPort );
               }
            } );
            result.push( {} );
         } else if( cmd == "default switchport tap default group" ) {
            $.each( tapAggGroupDetailResponse.groups, function( groupName, group ) {
               if( currInterface in group.tapPortStatuses ) { 
                  delete group.tapPortStatuses[ currInterface ];
               }
            } );
            
            if( currInterface in intfTapDetailResponse.tapProperties ) {
               intfTapDetailResponse.tapProperties[ currInterface ].details.defaultGroup = '---';
            }
            result.push( {} );
         } else if( cmd == "default switchport mode" ) {
            if( currInterface in intfTapDetailResponse.tapProperties ) {
               delete intfTapDetailResponse.tapProperties[ currInterface ];
            }
            result.push( {} );
         } else if( cmd.match( "clear counters .* session" ) ) {
            var intf = cmd.match( /clear counters (.*) session/ )[ 1 ];
            allIntfResponse.interfaces[ intf ].interfaceCounters = $.extend( true, {}, zeroedIntfResponse );
            result.push( {} );
         }
      }
      if( result.length === 0 ) {
         return [ 400, "Unknown commands :-O" ];
      } else {
         return [ 200, { "jsonrpc": parsedData.jsonrpc, "id": parsedData.id,  "result": result } ];
      }
   } );
} ] );


var versionResponse = { "modelName": "DCS-7508",
                        "internalVersion": "(unknown)",
                        "systemMacAddress": "00:1c:73:3c:e3:96",
                        "serialNumber": "HSH13465093",
                        "memTotal": 132142716,
                        "bootupTimestamp": 1426204801,
                        "memFree": 21330448,
                        "version": "4.15.0F",
                        "architecture": "(unknown)",
                        "internalBuildId": "(unknown)",
                        "hardwareRevision": "Not available" };

var zeroedIntfResponse = {
   "outBroadcastPkts": 0,
   "outUcastPkts": 0,
   "totalOutErrors": 0,
   "inMulticastPkts": 0,
   "inBroadcastPkts": 0,
   "outputErrorsDetail": {
      "deferredTransmissions": 0,
      "txPause": 0,
      "collisions": 0,
      "lateCollisions": 0
   },
   "outOctets": 0,
   "outDiscards": 0,
   "inOctets": 0,
   "inUcastPkts": 0,
   "inputErrorsDetail": {
      "runtFrames": 0,
      "rxPause": 0,
      "fcsErrors": 0,
      "alignmentErrors": 0,
      "giantFrames": 0,
      "symbolErrors": 0
   },
   "linkStatusChanges": 0,
   "outMulticastPkts": 0,
   "totalInErrors": 0,
   "inDiscards": 0,
   "counterRefreshTime": 0
};

var intfResponse = { "interfaceAddress": [],
                     "name": "EthernetXXX",
                     "duplex": "duplexFull",
                     "autoNegotiate": "unknown",
                     "burnedInAddress": "00:00:01:01:00:02",
                     "mtu": 9212,
                     "hardware": "ethernet",
                     "interfaceStatus": "connected",
                     "bandwidth": 10000000000,
                     "forwardingModel": "bridged",
                     "lineProtocolStatus": "up",
                     "interfaceCounters": {
                        "outBroadcastPkts": 0,
                        "outUcastPkts": 0,
                        "totalOutErrors": 0,
                        "inMulticastPkts": 6,
                        "inBroadcastPkts": 0,
                        "outputErrorsDetail": {
                           "deferredTransmissions": 0,
                           "txPause": 0,
                           "collisions": 0,
                           "lateCollisions": 0
                        },
                        "outOctets": 5454681,
                        "outDiscards": 0,
                        "inOctets": 492,
                        "inUcastPkts": 0,
                        "inputErrorsDetail": {
                           "runtFrames": 0,
                           "rxPause": 0,
                           "fcsErrors": 0,
                           "alignmentErrors": 0,
                           "giantFrames": 0,
                           "symbolErrors": 0
                        },
                        "linkStatusChanges": 0,
                        "outMulticastPkts": 44347,
                        "totalInErrors": 0,
                        "inDiscards": 0,
                        "counterRefreshTime": 0
                     },
                     "interfaceStatistics": {
                        "inBitsRate": 1000000000,
                        "outBitsRate": 6000000000,
                        "inPktsRate": 7000000,
                        "updateInterval": 300,
                        "outPktsRate": 800000
                     },
                     "physicalAddress": "00:00:01:01:00:02",
                     "description": "Hello :-D" };

// Use a fixed seed for the tour for consistency, otherwise random
var seed = parameters.autoStartTour ? 69 : Math.random();

// This is a simple, seeded PRNG for repeatability when used with the introjs tour.
// We want to make sure the same ports, connections, etc. get created each time.
function random() {
   var x = Math.sin(seed++) * 10000;
   return x - Math.floor(x);
}

function pickRandom( list ) {
   return list[ Math.floor(random() * list.length ) ];
}

function randInRange( min, max ) {
   return Math.floor(random() * (max - min + 1)) + min;
}

function partition( probability, list, partitionA, partitionB ) {
   // probability is a number between 0-1, indicating probability a
   // given element of list is included in partitionA. Otherwise it
   // will be included in partitionB.
    probability = 0.5;
   for( var i = 0; i < list.length; i++ ) {
      if( random() <= probability ) {
         partitionA.push( list[ i ] );
      } else {
         partitionB.push( list[ i ] );
      }
   }
}

var interfacesTransceiverResponse = {
   "interfaces" : {
      "Ethernet1": { "vendorSn" : "foo", 
                      "mediaType": "foo2", 
                      "updateTime": 0,
                      "temperature": 37.1,
                      "voltage": 3.5,
                      "txBias": 13.1,
                      "txPower": 10.3,
                      "rxPower": 43.1
                      },
      "Ethernet2": { "vendorSn" : "foo", 
                      "mediaType": "foo2", 
                      "updateTime": 0,
                      "temperature": 37.1,
                      "voltage": 3.5,
                      "txBias": 13.1,
                      "rxPower": 43.1
                      },
      "Ethernet3": { "vendorSn" : "foo", 
                      "mediaType": "foo2", 
                      "updateTime": 0,
                      "temperature": 37.1,
                      "voltage": 3.5,
                      "txBias": 13.1,
                      "txPower": 10.3,
                      }
   }
};

// Set the number of standalone interface (e.g., Ethernet1, not modular interfaces like Ethernet2/3/4)
var numStandaloneEthIntfs = parameters.numEthIntfs;
var numPortChannelIntfs = parameters.numPortChannelIntfs;

var numLineCards = parameters.numModularLineCards;
var numInterfacesPerLineCard = parameters.numModularIntfsPerLineCard;

var intfStatuses = [ '', 'connected', 'disabled', 'errdisabled' ];
var intfDescriptions = [ '', 'core-connection-ex12789-long-desc',
                         'DC Monitor', 'NetView #154' ];
var allIntfResponse = { "interfaces": { } };
var i, j, intfDetails;
for( i = 1; i <= numStandaloneEthIntfs; i++ ) {
   intfDetails = $.extend( true, {}, intfResponse );
   intfDetails.name = 'Ethernet' + i;
   intfDetails.interfaceStatus = pickRandom( intfStatuses );
   intfDetails.description = pickRandom( intfDescriptions );
   allIntfResponse.interfaces[ 'Ethernet' + i ] = intfDetails;
}

// Port Channels
for( i = 1; i <= numPortChannelIntfs; i++ ) {
   intfDetails = $.extend( true, {}, intfResponse );
   intfDetails.name = 'Port-Channel' + i;
   intfDetails.interfaceStatus = pickRandom( intfStatuses );
   intfDetails.description = pickRandom( intfDescriptions );
   allIntfResponse.interfaces[ 'Port-Channel' + i ] = intfDetails;
}

for( i = 1; i <= numInterfacesPerLineCard; i++ ) {
   for ( j = 1; j <= numLineCards; j++ ) {
      intfDetails = $.extend( true, {}, intfResponse );
      intfDetails.name = 'Ethernet' + j + '/' + i;
      intfDetails.interfaceStatus = pickRandom( intfStatuses );
      intfDetails.description = pickRandom( intfDescriptions );
      allIntfResponse.interfaces[ 'Ethernet' + j + '/' + i ] = intfDetails;
   }
}


var intfStatusResponse = {
    "vlanInformation": {
        "interfaceMode": "tap",
        "interfaceForwardingModel": "bridged"
    },
    "bandwidth": 10000000000,
    "interfaceType": "10GBASE-CR",
    "description": "",
    "autoNegotiateActive": false,
    "duplex": "duplexFull",
    "autoNegotigateActive": false,
    "linkStatus": "connected",
    "lineProtocolStatus": "up"
};

var intfCountersResponse = {
    "outBroadcastPkts": 0,
    "outUcastPkts": 0,
    "outMulticastPkts":0,
    "outOctets": 5454681,
    "outDiscards": 0,
    "totalOutErrors": 0,
    "inBroadcastPkts": 0,
    "inUcastPkts": 0,
    "inMulticastPkts": 6,
    "inOctets": 492,
    "inDiscards": 0,
    "totalInErrors": 0
};

var allIntfStatusResponse = { "interfaceStatuses": {} };
var allIntfDetails;

// Add standalone interfaces
for( i = 1; i <= numStandaloneEthIntfs; i++ ) {
   allIntfDetails = allIntfResponse.interfaces[ 'Ethernet' + i ];
   intfDetails = $.extend( true, {}, intfStatusResponse );
   // Copy the details from the allIntfResponse so we are consistent across equivalent fields
   intfDetails.linkStatus = allIntfDetails.interfaceStatus;
   intfDetails.description = allIntfDetails.description;
   intfDetails.bandwidth = allIntfDetails.bandwidth;
   allIntfStatusResponse.interfaceStatuses[ 'Ethernet' + i ] = intfDetails;
}

// Add modular interfaces
for( i = 1; i <= numInterfacesPerLineCard; i++ ) {
   for ( j = 1; j <= numLineCards; j++ ) {
      allIntfDetails = allIntfResponse.interfaces[ 'Ethernet' + j + '/' + i ];
      intfDetails = $.extend( true, {}, intfStatusResponse );
      // Copy the details from the allIntfResponse so we are consistent across equivalent fields
      intfDetails.linkStatus = allIntfDetails.interfaceStatus;
      intfDetails.description = allIntfDetails.description;
      intfDetails.bandwidth = allIntfDetails.bandwidth;
      allIntfStatusResponse.interfaceStatuses[ 'Ethernet' + j + '/' + i ] = intfDetails;
   }
}

// Add port channel interfaces
for( i = 1; i <= numPortChannelIntfs; i++ ) {
   allIntfDetails = allIntfResponse.interfaces[ 'Port-Channel' + i ];
   intfDetails = $.extend( true, {}, intfStatusResponse );
   // Copy the details from the allIntfResponse so we are consistent across equivalent fields
   intfDetails.linkStatus = allIntfDetails.interfaceStatus;
   intfDetails.description = allIntfDetails.description;
   intfDetails.bandwidth = allIntfDetails.bandwidth;
   allIntfStatusResponse.interfaceStatuses[ 'Port-Channel' + i ] = intfDetails;
}

var allIntfCountersResponse = { "interfaces": {} };
var intfCounters;
for( i = 1; i <= numStandaloneEthIntfs; i++ ) {
   intfCounters = $.extend( true, {}, intfCountersResponse );
   allIntfCountersResponse.interfaces[ 'Ethernet' + i ] = intfCounters;
}

for( i = 1; i <= numPortChannelIntfs; i++ ) {
   intfCounters = $.extend( true, {}, intfCountersResponse );
   allIntfCountersResponse.interfaces[ 'Port-Channel' + i ] = intfCounters;
}

// Something is a bit wrong with this logic. It almost works, but is causing errors in the autoupdating (and somehow the no-default-group is never set in this logic:

// Calculate groups:
var groups = [];

var tapIntfs = [], toolIntfs = [], unusedIntfs = [], placeholder = [];
// Assign Tap interfaces:
partition( 0.33, Object.keys( allIntfResponse.interfaces ), tapIntfs, placeholder );
// And now assign tool/unused interfaces:
partition( 0.5, placeholder, toolIntfs, unusedIntfs );

// Create the base groups in tapAggGroupDetailResponse
var tapAggGroupDetailResponse = { "groups": {} };

// Fill out Tap interfaces
var intfTapDetailResponse = { "tapProperties": {}, "toolProperties": {} };

// Fill out tool interfaces
var intfToolResponse = { "tapProperties": {}, "toolProperties": {} };

// Generate a random set of groups for a given interface to belong to
// The setup of groups that exists are in 
var generateToolGroups = function() {
   // Add this tap port to a random set of groups
   var memberGroups = [];
   partition( 0.3, groups, memberGroups, [] );
   for( j = 0; j < memberGroups.length; j ++ ) {
      // add this to the tapAggGroupDetailResponse
      tapAggGroupDetailResponse.groups[ memberGroups[j] ].tapPortStatuses[ tapIntfs[ i ] ] = { "statuses": [ "Active" ] };
   }
   return memberGroups;
};

var generateToolPorts = function() {
   var toolPorts = [];
   var portNum;
   var numEtToolPorts = randInRange(0, 2);
   var numPoToolPorts = randInRange(0, 2);
   var i;

   // Set these ranges lower for a better chance of being in the same bundle
   var max = 5;
   var maxRandomEthIntfRange = numStandaloneEthIntfs < max ? numStandaloneEthIntfs : max;
   var maxRandomPoIntfRange = numPortChannelIntfs < max ? numPortChannelIntfs : max;

   // TODO: Need to handle the case where an interface is set as 
   //       a toolPort, but is not actually configured as a tool yet.
   //       In this case, we don't want to draw lines to it.
   for( i=0; i<numEtToolPorts; i++ ) {
      portNum = randInRange(1, maxRandomEthIntfRange);
      if( toolPorts.indexOf( "Ethernet" + portNum ) < 0 ) {
         toolPorts.push("Ethernet" + portNum);
      }
   }
   
   for( i=0; i<numPoToolPorts; i++ ) {
      portNum = randInRange(1, maxRandomPoIntfRange);
      if( toolPorts.indexOf( "Port-Channel" + portNum ) < 0 ) {
         toolPorts.push("Port-Channel" + portNum);
      }
   }

   return toolPorts;
};

function generateGroupName( len ) {
   var name = "G";
   for ( var i = 1 ; i < len ; i++ ) {
      name += ( i % 10 );
   }
   return name;
}

if( CREATE_INITIAL_GROUPS ) {
   groups = [ "SecurityMonitor", generateGroupName( 230 ) ];
   partition( 0.5, [ "VOIPRecorder", "PacketSniffer", "NetAnalyzer", "TradeAuditor" ], groups, [] );

   for( i = 0; i < groups.length; i++ ) {
      tapAggGroupDetailResponse.groups[ groups[ i ] ] = { "toolPortStatuses": {},
                                                          "tapPortStatuses": {} };
   }
   for( i = 0; i < tapIntfs.length; i++ ) {
      intfTapDetailResponse.tapProperties[ tapIntfs[ i ] ] = {
            "allowedVlans": "All",
            "nativeVlan": 1,
            "details": {
               "defaultGroup": memberGroups ? memberGroups[0] : "---",
               "aclsAppliedPerType": {},
               "groups": generateToolGroups(),
               "toolPorts": generateToolPorts()
            },
            "truncationSize": 0,
            "portIdentity": 1,
            "linkStatus": "disabled",
            "configuredMode": "tap"
      };
   }

   for( i = 0; i < toolIntfs.length; i++ ) {
      intfToolResponse.toolProperties[ toolIntfs[ i ] ] = {
         "allowedVlans": "All",
         "timestampMode": "None",
         "identificationTag": "Off",
         "linkStatus": "tool",
         "configuredMode": "tool",
         "details": {
            "truncationSize": 0,
            "aclsAppliedPerType" : {}
         }
      };
   
      // Add this tool port to a random set of groups
      var memberGroups = [];
      partition( 0.3, groups, memberGroups, [] );
      for( j = 0; j < memberGroups.length; j ++ ) {
         // add this to the tapAggGroupDetailResponse
         tapAggGroupDetailResponse.groups[ memberGroups[j] ].toolPortStatuses[ toolIntfs[ i ] ] = { "statuses": [ "Active" ] };

      }
   }
}

var generateRandomIp = function() {
   return Math.floor( ( random() * 1000 ) ) % 255 + '.' +
          Math.floor( ( random() * 1000 ) ) % 255 + '.' +
          Math.floor( ( random() * 1000 ) ) % 255 + '.' +
          Math.floor( ( random() * 1000 ) ) % 255;
};

var generateRandomHost = function() {
   var randNum = random();
   if( randNum < 0.1 ) {
      return "any ";
   } else if ( randNum < 0.6 ) {
      return generateRandomIp() +"/24 ";
   } else {
      return generateRandomIp() + " " + generateRandomIp() + " ";
   }
};

var generateRandomAclRuleText = function() {
   var ruleText = "";
   var randNum = random();
   if( randNum < 0.1 ) {
      return "remark This is a remark";
   } else if( randNum < 0.6 ) {
      ruleText += "permit ";
   } else {
      ruleText += "deny ";
   }
   
   ruleText += "ip " + generateRandomHost() + " " + generateRandomHost();
   return ruleText;
};

var generateAcl = function( name, type ) {
   var newAcl = { name: name,
         standard: false, 
         readonly: random() > 0.95 ? true : false,
         type: type,
         sequence: [] };

   for( var j = 1; j < 100; j++ ) {
      var acl = { sequenceNumber: j * 10, text: generateRandomAclRuleText() };
      if( acl.text.indexOf('remark') !== 0) {
         // Real rules will have this field while comments will not
         acl.ruleFilter = 'dummy';
      }
      newAcl.sequence.push( acl );
   }
   return newAcl;
};

var ipAcls = { "aclList" : [] };
var ipv6Acls = { "aclList" : [] };
var macAcls = { "aclList" : [] };

for( i = 0; i < 30; i++ ) {
   ipAcls.aclList.push( generateAcl( "myAwesomeIpAcl" + i, "Ip4Acl" ) );
}

for( i = 0; i < 3; i++ ) {
   ipv6Acls.aclList.push( generateAcl( "ipv6Acl" + i, "Ip6Acl" ) );
}

for( i = 0; i < 3; i++ ) {
   macAcls.aclList.push( generateAcl( "macAcl" + i, "MacAcl" ) );
}

// Class Maps
var tapAggClassMaps = { "classMaps": {} };

var generateClassMap = function( name, acls ) {
   var aclEntry;
   var sequenceNum;
   var numAcls = randInRange(1, 5);

   // Create some acls if nothing given
   if( !acls ) {
      acls = {};
      for (var i=1; i<=numAcls; i++) {
         sequenceNum = "" + (i*10);
         acls[ sequenceNum ] = { name: "myAcl" + i };
      }
   }

   return {
      "matchCondition": "matchConditionAny",
      "match": {
         "matchIpAccessGroup": {
            "option": "matchIpAccessGroup",
            "ip6Rule": {},
            "macRule": {},
            "ipRule": {},
            "acl": acls
         }
      }
   };
};

var createClassMap = function( name, acls ) {
   tapAggClassMaps.classMaps[ name ] = generateClassMap( name, acls );
   return tapAggClassMaps.classMaps[ name ];
};

var removeClassMap = function( name ) {
   delete tapAggClassMaps.classMaps[ name ];
};

// TODO: Take sequenceNumber into account
var addAclToClassMap = function( classMapName, sequenceNumber, type, aclName ) {
   var classMap = tapAggClassMaps.classMaps[ classMapName ];
   if( classMap ) {
      var acls = classMap.match.matchIpAccessGroup.acl;
      acls[ "" + sequenceNumber ] = { name: aclName };
   }
};

var numInitialClassMaps = 10;
for( i = 1; i <= numInitialClassMaps; i++ ) {
   var name = "classMap" + i;
   createClassMap( name );
}


// Policy Maps
var tapAggPolicyMaps = { "policyMaps": {} };

var generateRandomPolicyMapRule = function( name ) {
   var aggGroups = groups.slice();
   var numToRemove = aggGroups.length - randInRange( 0, aggGroups.length );
   for( var i=0; i<numToRemove; i++ ) {
      aggGroups.splice( randInRange( 0, aggGroups.length - 1 ), 1 );
   }
   
   var aggInterfaces = toolIntfs.slice();
   var maxIntfs = aggInterfaces.length < 5 ? aggInterfaces.length : 5;
   numToRemove = aggInterfaces.length - ( maxIntfs - randInRange( 0, maxIntfs ) );
   for( i=0; i<numToRemove; i++ ) {
      aggInterfaces.splice( randInRange( 0, aggInterfaces.length - 1 ), 1 );
   }

   var vlanId;
   var emptyVlanChance = randInRange(1, 100);
   if( emptyVlanChance >= 30) {
      vlanId = randInRange(1, 200);
   }

   return {
      "name": "classMap" + randInRange(1, 10),  // Name of the class map to use for packet selection
      "configuredAction": {
         "setAggregationGroup": {
            "actionType": "setAggregationGroup",
            "aggGroup": aggGroups
         },
         "setAggregationInterface": {
            "actionType": "setAggregationInterface",
            "aggInterface": aggInterfaces.join(",")
         },
         "setIdentityTag": {
            "actionType": "setIdentityTag",
            "idTag": vlanId
         }
      }
   };
};

var createEmptyPolicyMap = function( name ) {
   return {
      classMap: {},  // The rules go here
      name: name,
      configuredIngressIntfs: [],
      appliedIngressIntfs: [],
      mapType: "mapTapAgg"
   };
};

var generateRandomPolicyMap = function( name ) {
   var policy = createEmptyPolicyMap( name );

   // Select some interfaces at random to be configured
   var numConfiguredIntfs = randInRange(0, 3);
   for( var i=0; i<numConfiguredIntfs; i++ ) {
      var intfNum = randInRange( 0, 3 );
      // Don't add duplicates
      if( policy.configuredIngressIntfs.indexOf( "Ethernet" + (intfNum+1) ) < 0 ) {
         policy.configuredIngressIntfs.push( "Ethernet" + (intfNum+1) );
      }
   }

   // Generate classMap rules
   var numRulesToAdd = randInRange(1, 5);
   for( i=1; i<=numRulesToAdd; i++) {
      var sequenceNumber = "" + (i * 10);
      var rule = generateRandomPolicyMapRule( name );
      policy.classMap[ sequenceNumber ] = rule;
   }


/*
   "classMap": {
      "10": {
         "name": "t-class_1",
         "configuredAction": {
            "setAggregationGroup": {
               "actionType": "setAggregationGroup",
               "aggGroup": "t-grp1"
            },
            "setIdentityTag": {
               "actionType": "setIdentityTag",
               "idTag": 111
            }
         },
      },
   },
   "name": "t-policy_1",
   "configuredIngressIntfs": [
                  "Ethernet1"
   ],
   "appliedIngressIntfs": [],
   "mapType": "mapTapAgg"
*/

   return policy;
};

var createPolicyMap = function( name, createEmpty ) {
   tapAggPolicyMaps.policyMaps[ name ] = createEmpty ? createEmptyPolicyMap( name ) : generateRandomPolicyMap( name );
   return tapAggPolicyMaps.policyMaps[ name ];
};

var removePolicyMap = function( name ) {
   delete tapAggPolicyMaps.policyMaps[ name ];
};

var getOrCreateClassMapInPolicyMap = function( policyMap, sequenceNum, classMapName ) {
   var classMap = policyMap.classMap[ sequenceNum ];
   if( !classMap ) {
      classMap = {
         "name": classMapName,
         "configuredAction": {}  // These will get added by subsequent commands
      };
      policyMap.classMap[ sequenceNum ] = classMap;
   }

   return classMap;
};

var setAggregationGroupsForClassMapInPolicyMap = function( classMap, groups ) {
   var actions = classMap.configuredAction;
   if( !actions.setAggregationGroup ) {
      actions.setAggregationGroup = {
         actionType: "setAggregationGroup",
         aggGroup: [],
         aggIntf: []
      };
   }

   // Add the groups to the string
   $.each( groups, function( index, groupName ) {
      var i = actions.setAggregationGroup.aggGroup.indexOf( groupName );
      if( i < 0 ) {
         actions.setAggregationGroup.aggGroup.push( groupName );
      }
      // else, the group name already exists in the list
   } );
};

var setToolPortIntfsForClassMapInPolicyMap = function( classMap, toolPortIntfs ) {
   var actions = classMap.configuredAction;
   if( !actions.setAggregationGroup ) {
      actions.setAggregationGroup = {
         actionType: "setAggregationGroup",
         aggGroup: [],
         aggIntf: []
      };
   }

   // Add the port intfs to the string
   $.each( toolPortIntfs, function( index, portName ) {
      var i = actions.setAggregationGroup.aggIntf.indexOf( portName );
      if( i < 0 ) {
         actions.setAggregationGroup.aggIntf.push( portName );
      }
      // else, the port name already exists in the list
   } );
};

var setVlanIdForClassMapInPolicyMap = function( classMap, vlanId ) {
   var actions = classMap.configuredAction;

   actions.setIdentityTag = {
      actionType: "setIdentityTag",
      idTag: vlanId
   };
};

var numInitialPolicyMaps = 3;
for( i = 1; i <= numInitialPolicyMaps; i++ ) {
   var name = "policyMap" + i;
   createPolicyMap( name, false );
}

var setTapIntfPolicyMap = function( intfName, policyMapName ) {
   var policyMap = tapAggPolicyMaps.policyMaps[ policyMapName ];
   if( policyMap ) {
      // If this interface is not already in the list, then add it
      if( policyMap.configuredIngressIntfs.indexOf( intfName ) < 0 ) {
         policyMap.configuredIngressIntfs.push( intfName );
      }
   }
};

// Need to look through all policy maps to remove this interface from whichever one it is in
var unsetTapIntfPolicyMap = function( intfName ) {
   $.each(tapAggPolicyMaps.policyMaps, function( policyIndex, policyMap ) {
      var index = policyMap.configuredIngressIntfs.indexOf( intfName );
      if( index >= 0 ) {
         policyMap.configuredIngressIntfs.splice(index, 1);
      }
   } );
};

var generateIntfCounters = function( counters, bandwidth ) {
   var currRefreshTime = ( new Date() ).getTime() / 1000;
   var previousRefreshTime = counters.counterRefreshTime ? counters.counterRefreshTime : currRefreshTime;
   var timeDelta = ( currRefreshTime - previousRefreshTime );
   counters.counterRefreshTime = currRefreshTime;
           
   var inBitRate = Math.floor( ( ( timeDelta * random() ) ) * bandwidth );
   var outBitRate = Math.floor( ( ( timeDelta * random() ) ) * bandwidth );

   counters.outUcastPkts += Math.floor( inBitRate / 160 );
   counters.inUcastPkts += Math.floor( outBitRate / 160 );
   counters.inOctets += Math.floor( inBitRate / 8 );
   counters.outOctets += Math.floor( outBitRate/ 8 );
};

var queueLengthEnabledResponse = {
   "reportTime": 1382648111.042279,
   "globalHitCount": 0,
   "bytesPerTxmpSegment": 480,
   "lanzEnabled": true,
   "platformName": "FocalPointV2",
   "entryList": [
      {
         "interface": "Et1",
         "txDrops": 31337086,
         "entryTime": 1420235459.32
      },
      {
         "interface": "Et1",
         "txDrops": 71421225,
         "entryTime": 1420235459.32
      },
      {
         "interface": "Et1",
         "txDrops": 31316527,
         "entryTime": 1420235454.32
      }
   ]
};

var queueLengthDisabledResponse = {
   "reportTime": 1382648111.042279,
   "globalHitCount": 0,
   "bytesPerTxmpSegment": 480,
   "lanzEnabled": false,
   "platformName": "FocalPointV2",
   "entryList": []
};

var queueLengthDisabledResponseCsv = { output: "queue-monitor length is disabled.\n " };
var queueLengthEnabledResponseCsv = { output: "\nReport generated at 2013-08-12 21:56:17\nType,Time,Interface,Duration(usecs),Queue-Length,Time-Of-Max-Queue(usecs),Latency(usecs),,Tx-Drops\n S,2013-08-12 21:55:59.53203,Et4(1),N/A,559,N/A,51.875,0\n U,2013-08-12 21:55:59.53213,Et4(1),N/A,888,N/A,82.406,0\n U,2013-08-12 21:55:59.53222,Et4(1),N/A,1184,N/A,109.875,0\n U,2013-08-12 21:55:59.53230,Et4(1),N/A,1502,N/A,139.385,0\n U,2013-08-12 21:55:59.53239,Et4(1),N/A,1798,N/A,166.854,0\n U,2013-08-12 21:55:59.53248,Et4(1),N/A,2115,N/A,196.272,0\n U,2013-08-12 21:55:59.53257,Et4(1),N/A,2412,N/A,223.833,0\n U,2013-08-12 21:55:59.53265,Et4(1),N/A,2725,N/A,252.880,500000\n U,2013-08-12 21:55:59.53274,Et4(1),N/A,3018,N/A,280.070,0\n"};

var runningConfigResponse = { output: "! Command: show running-config\n! Time: Thu Jul 25 00:15:06 2013\n! device: ro153 (DCS-7150S-24, EOS-4.12.4-1360593.2013tapAggGui (engineering build))\n!\n! boot system flash:/EOS.swi\n!\nno lldp run\n!\nno logging console\n!\nhostname ro153\nip name-server vrf default 172.22.22.40\nip domain-name cs1.companynetworks.com\n!\nsnmp-server community public ro\n!\nspanning-tree mode mstp\n!\naaa authorization exec default local\n!\naaa root secret 5 $1$eSAEQi2k$Iln7/9Gz1owBtYmGNokKW0\naaa authentication policy local allow-nopassword-remote-login\n!\nusername ryan role ryan secret 5 $1$6h61DHnm$nN7I39fMsP.T0mzWtfnbe0\n!\ntap aggregation\n   mode exclusive\n!\nclock timezone PST8PDT\n!\ninterface Ethernet1\n   description Autoupdating is the bestest\n   switchport mode tap\n   switchport tap native vlan 7\n   switchport tap allowed vlan 5-6\n   switchport tap truncation 600\n   switchport tap default group siva\n!\ninterface Ethernet2\n   switchport mode tool\n   switchport tool group set foo siva\n!\ninterface Ethernet3\n   switchport mode tap\n   switchport tap default group foo\n!\ninterface Ethernet4\n   description Diego, can you see this\n   switchport mode tool\n   switchport tool allowed vlan 1-4\n   switchport tool identity dot1q\n!\ninterface Ethernet5\n!\ninterface Ethernet6\n   description Diego, can you see this\n   switchport mode tool\n   switchport tool group set foo siva\n!\ninterface Ethernet7\n   description Autoupdating is the bestest\n   switchport mode tool\n   switchport tool identity dot1q\n!\ninterface Ethernet8\n   description Diego, can you see this\n   switchport mode tap\n   switchport tap default group foo\n!\ninterface Ethernet9\n!\ninterface Ethernet10\n!\ninterface Ethernet11\n!\ninterface Ethernet12\n!\ninterface Ethernet13\n!\ninterface Ethernet14\n   switchport mode tap\n   switchport tap default group foo\n!\ninterface Ethernet15\n!\ninterface Ethernet16\n!\ninterface Ethernet17\n!\ninterface Ethernet18\n!\ninterface Ethernet19\n!\ninterface Ethernet20\n!\ninterface Ethernet21\n   description This is cool!\n   switchport mode tool\n!\ninterface Ethernet22\n!\ninterface Ethernet23\n!\ninterface Ethernet24\n!\ninterface Management1\n   ipv6 address fd7a:629f:52a4:13::d70/64\n   ip address 172.19.13.112/16\n!\nip route 172.17.0.0/16 172.19.0.1\nip route 172.18.0.0/16 172.19.0.1\nip route 172.20.0.0/16 172.19.0.1\nip route 172.22.0.0/16 172.19.0.1\n!\nipv6 route fd7a:629f:52a4::/48 fd7a:629f:52a4:13::2\n!\nno ip routing\n!\nmanagement api http-commands\n   no protocol https\n   protocol http\n   no shutdown\n!\n!\nend\n" };

var runningConfigDiffResponse = { output: "--- flash:/startup-config\n+++ system:/running-config\n@@ -14,26 +14,56 @@\n !\n spanning-tree mode mstp\n !\n+aaa authorization exec default local\n+!\n aaa root secret 5 $1$eSAEQi2k$Iln7/9Gz1owBtYmGNokKW0\n aaa authentication policy local allow-nopassword-remote-login\n+!\n+username ryan role ryan secret 5 $1$6h61DHnm$nN7I39fMsP.T0mzWtfnbe0\n+!\n+tap aggregation\n+   mode exclusive\n !\n clock timezone PST8PDT\n !\n interface Ethernet1\n+   description Autoupdating is the bestest\n+   switchport mode tap\n+   switchport tap native vlan 7\n+   switchport tap allowed vlan 5-6\n+   switchport tap truncation 600\n+   switchport tap default group siva\n !\n interface Ethernet2\n+   switchport mode tool\n+   switchport tool group set foo siva\n !\n interface Ethernet3\n+   switchport mode tap\n+   switchport tap default group foo\n !\n interface Ethernet4\n+   description Diego, can you see this\n+   switchport mode tool\n+   switchport tool allowed vlan 1-4\n+   switchport tool identity dot1q\n !\n interface Ethernet5\n !\n interface Ethernet6\n+   description Diego, can you see this\n+   switchport mode tool\n+   switchport tool group set foo siva\n !\n interface Ethernet7\n+   description Autoupdating is the bestest\n+   switchport mode tool\n+   switchport tool identity dot1q\n !\n interface Ethernet8\n+   description Diego, can you see this\n+   switchport mode tap\n+   switchport tap default group foo\n !\n interface Ethernet9\n !\n@@ -46,6 +76,8 @@\n interface Ethernet13\n !\n interface Ethernet14\n+   switchport mode tap\n+   switchport tap default group foo\n !\n interface Ethernet15\n !\n@@ -60,6 +92,8 @@\n interface Ethernet20\n !\n interface Ethernet21\n+   description This is cool!\n+   switchport mode tool\n !\n interface Ethernet22\n !\n@@ -80,5 +114,10 @@\n !\n no ip routing\n !\n+management api http-commands\n+   no protocol https\n+   protocol http\n+   no shutdown\n+!\n !\n end\n\n" };

var syslogMessages = { output: "2013-07-21T09:00:07.173517-07:00 a2-magnesium Stp: 469: %SPANTREE-6-INTERFACE_DEL: Interface PeerEthernet17 has been removed from instance Vl3908\n2013-07-21T09:00:07.173517-07:00 a2-magnesium Stp: 469: %SPANTREE-6-INTERFACE_DEL: Interface PeerEthernet17 has been removed from instance Vl3908\n2013-07-21T09:00:07.174366-07:00 a2-magnesium Stp: 470: %SPANTREE-6-INTERFACE_DEL: Interface PeerEthernet17 has been removed from instance Vl3923\n2013-07-21T09:00:07.399612-07:00 a2-magnesium Ebra: 471: %LINEPROTO-5-UPDOWN: Line protocol on Interface Ethernet22 (cn.e3/1), changed state to down\n2013-07-21T09:00:07.424313-07:00 a2-magnesium Stp: 472: %SPANTREE-6-INTERFACE_DEL: Interface Ethernet22 has been removed from instance Vl3908\n2013-07-21T09:00:07.424368-07:00 a2-magnesium Stp: 473: %SPANTREE-6-INTERFACE_DEL: Interface Ethernet22 has been removed from instance Vl282\n2013-07-21T09:00:07.424387-07:00 a2-magnesium Stp: 474: %SPANTREE-6-INTERFACE_DEL: Interface Ethernet22 has been removed from instance Vl3923\n2013-07-21T09:00:07.424403-07:00 a2-magnesium Stp: 475: %SPANTREE-6-INTERFACE_DEL: Interface Ethernet22 has been removed from instance Vl283\n2013-07-21T09:00:07.529410-07:00 a2-magnesium Stp: 476: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is PeerEthernet18, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.529867-07:00 a2-magnesium Stp: 477: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from discarding to learning\n2013-07-21T09:00:07.530558-07:00 a2-magnesium Stp: 478: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.534805-07:00 a2-magnesium Stp: 479: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is PeerEthernet18, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.535986-07:00 a2-magnesium Stp: 480: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.539197-07:00 a2-magnesium Stp: 481: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is PeerEthernet18, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.543611-07:00 a2-magnesium Stp: 482: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.543663-07:00 a2-magnesium Stp: 483: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is PeerEthernet18, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.546272-07:00 a2-magnesium Stp: 484: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from discarding to learning\n2013-07-21T09:00:07.553945-07:00 a2-magnesium Stp: 485: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:00:07.556609-07:00 a2-magnesium Stp: 486: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:00:07.665292-07:00 a2-magnesium Stp: 487: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.665972-07:00 a2-magnesium Stp: 488: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl282: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.666250-07:00 a2-magnesium Stp: 489: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3923: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:07.667808-07:00 a2-magnesium Stp: 490: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.668812-07:00 a2-magnesium Stp: 491: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet9 instance Vl283 moving from forwarding to discarding\n2013-07-21T09:00:07.669205-07:00 a2-magnesium Stp: 492: %SPANTREE-6-INTERFACE_STATE: Interface Port-Channel4 instance Vl283 moving from forwarding to discarding\n2013-07-21T09:00:07.670210-07:00 a2-magnesium Stp: 493: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:0f:6a:80\n2013-07-21T09:00:07.672095-07:00 a2-magnesium Stp: 494: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is PeerEthernet9, new root bridge mac address is 00:1c:73:0f:6a:80\n2013-07-21T09:00:07.672627-07:00 a2-magnesium Stp: 495: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet9 instance Vl283 moving from forwarding to discarding\n2013-07-21T09:00:07.673370-07:00 a2-magnesium Stp: 496: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Port-Channel4, new root bridge mac address is 00:1c:73:0b:a8:0e\n2013-07-21T09:00:07.674850-07:00 a2-magnesium Stp: 497: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.676530-07:00 a2-magnesium Stp: 498: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:0f:6a:80\n2013-07-21T09:00:07.677916-07:00 a2-magnesium Stp: 499: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is PeerEthernet9, new root bridge mac address is 00:1c:73:0b:a8:0e\n2013-07-21T09:00:07.679339-07:00 a2-magnesium Stp: 500: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:00:07.680638-07:00 a2-magnesium Stp: 501: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet9, new root bridge mac address is 00:1c:73:0f:6a:80\n2013-07-21T09:00:07.681667-07:00 a2-magnesium Stp: 502: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is PeerEthernet9, new root bridge mac address is 00:1c:73:0b:a8:0e\n2013-07-21T09:00:07.682790-07:00 a2-magnesium Stp: 503: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Port-Channel4, new root bridge mac address is 00:1c:73:0b:a8:0e\n2013-07-21T09:00:07.719739-07:00 a2-magnesium Stp: 504: %SPANTREE-6-INTERFACE_STATE: Interface Port-Channel4 instance Vl283 moving from discarding to forwarding\n2013-07-21T09:00:09.568107-07:00 a2-magnesium Stp: 505: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from forwarding to discarding\n2013-07-21T09:00:09.684239-07:00 a2-magnesium Stp: 506: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet9 instance Vl283 moving from discarding to learning\n2013-07-21T09:00:09.689617-07:00 a2-magnesium Stp: 507: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet9 instance Vl283 moving from learning to forwarding\n2013-07-21T09:00:09.715284-07:00 a2-magnesium Stp: 508: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet9 instance Vl283 moving from discarding to learning\n2013-07-21T09:00:09.722004-07:00 a2-magnesium Stp: 509: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet9 instance Vl283 moving from learning to discarding\n2013-07-21T09:00:11.567188-07:00 a2-magnesium Stp: 510: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from discarding to learning\n2013-07-21T09:00:11.573087-07:00 a2-magnesium Stp: 511: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:00:11.715293-07:00 a2-magnesium Stp: 512: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet9 instance Vl283 moving from discarding to learning\n2013-07-21T09:00:11.766446-07:00 a2-magnesium Stp: 513: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet9 instance Vl283 moving from learning to forwarding\n2013-07-21T09:00:12.516555-07:00 a2-magnesium PortSec: 514: %ETH-4-HOST_FLAPPING: Host 00:1c:73:0c:55:d9 in VLAN 3908 is flapping between interface Port-Channel1 and interface Ethernet18 (message repeated 34 times in 21603.9 secs)\n2013-07-21T09:00:15.568726-07:00 a2-magnesium Stp: 515: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is (none), new root bridge mac address is 02:1c:73:00:13:19 (this switch)\n2013-07-21T09:00:15.573557-07:00 a2-magnesium Stp: 516: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from forwarding to discarding\n2013-07-21T09:00:15.573609-07:00 a2-magnesium Stp: 517: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from forwarding to discarding\n2013-07-21T09:00:15.586691-07:00 a2-magnesium Stp: 518: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from discarding to learning\n2013-07-21T09:00:15.590562-07:00 a2-magnesium Stp: 519: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:00:16.132042-07:00 a2-magnesium Stp: 520: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from discarding to learning\n2013-07-21T09:00:16.136992-07:00 a2-magnesium Stp: 521: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:00:17.771166-07:00 a2-magnesium PortSec: 522: %ETH-4-HOST_FLAPPING: Host 00:1c:73:0c:55:d9 in VLAN 3908 is flapping between interface Ethernet18 and interface Port-Channel1 (message repeated 10 times in 5.25433 secs)\n2013-07-21T09:00:38.637184-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.46, interface 172.17.254.154 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T09:00:44.169278-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.37, interface 172.17.254.93 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T09:01:22.258886-07:00 a2-magnesium Ebra: 523: %LINEPROTO-5-UPDOWN: Line protocol on Interface Ethernet22 (cn.e3/1), changed state to up\n2013-07-21T09:01:22.272380-07:00 a2-magnesium Stp: 524: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port Ethernet22.\n2013-07-21T09:01:22.272942-07:00 a2-magnesium Stp: 525: %SPANTREE-6-INTERFACE_ADD: Interface Ethernet22 has been added to instance Vl3908\n2013-07-21T09:01:22.273989-07:00 a2-magnesium Stp: 526: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port Ethernet22.\n2013-07-21T09:01:22.274404-07:00 a2-magnesium Stp: 527: %SPANTREE-6-INTERFACE_ADD: Interface Ethernet22 has been added to instance Vl282\n2013-07-21T09:01:22.276441-07:00 a2-magnesium Stp: 528: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port Ethernet22.\n2013-07-21T09:01:22.277128-07:00 a2-magnesium Stp: 529: %SPANTREE-6-INTERFACE_ADD: Interface Ethernet22 has been added to instance Vl3923\n2013-07-21T09:01:22.278238-07:00 a2-magnesium Stp: 530: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port Ethernet22.\n2013-07-21T09:01:22.278707-07:00 a2-magnesium Stp: 531: %SPANTREE-6-INTERFACE_ADD: Interface Ethernet22 has been added to instance Vl283\n2013-07-21T09:01:24.966698-07:00 a2-magnesium Stp: 532: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl282: new root interface is Ethernet22, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:01:24.966753-07:00 a2-magnesium Stp: 533: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl282 moving from discarding to learning\n2013-07-21T09:01:24.970837-07:00 a2-magnesium Stp: 534: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl282 moving from learning to forwarding\n2013-07-21T09:01:24.979905-07:00 a2-magnesium Stp: 535: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3923: new root interface is Ethernet22, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:01:24.980155-07:00 a2-magnesium Stp: 536: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl3923 moving from discarding to learning\n2013-07-21T09:01:24.984757-07:00 a2-magnesium Stp: 537: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl3923 moving from learning to forwarding\n2013-07-21T09:01:25.012116-07:00 a2-magnesium Stp: 538: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl3908: new root interface is Ethernet22, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:01:25.012493-07:00 a2-magnesium Stp: 539: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl3908 moving from discarding to learning\n2013-07-21T09:01:25.017764-07:00 a2-magnesium Stp: 540: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl3908 moving from learning to forwarding\n2013-07-21T09:01:25.199784-07:00 a2-magnesium Stp: 541: %SPANTREE-6-ROOTCHANGE: Root changed for instance Vl283: new root interface is Ethernet22, new root bridge mac address is 00:1c:73:03:13:40\n2013-07-21T09:01:25.200209-07:00 a2-magnesium Stp: 542: %SPANTREE-6-INTERFACE_STATE: Interface Port-Channel4 instance Vl283 moving from forwarding to discarding\n2013-07-21T09:01:25.200438-07:00 a2-magnesium Stp: 543: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl283 moving from discarding to learning\n2013-07-21T09:01:25.207469-07:00 a2-magnesium Stp: 544: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet22 instance Vl283 moving from learning to forwarding\n2013-07-21T09:01:25.213911-07:00 a2-magnesium Stp: 545: %SPANTREE-6-INTERFACE_STATE: Interface Port-Channel4 instance Vl283 moving from discarding to forwarding\n2013-07-21T09:01:26.891716-07:00 a2-magnesium Lldp: 546: %LLDP-5-NEIGHBOR_NEW: LLDP neighbor with chassisId 001c.7303.1340 and portId 'Ethernet3/1' added on interface Ethernet22\n2013-07-21T09:01:27.052616-07:00 a2-magnesium Stp: 547: %SPANTREE-6-INTERFACE_STATE: Interface Ethernet18 instance Vl3908 moving from forwarding to discarding\n2013-07-21T09:01:27.053168-07:00 a2-magnesium Stp: 548: %SPANTREE-6-INTERFACE_STATE: Interface PeerEthernet18 instance Vl3908 moving from forwarding to discarding\n2013-07-21T09:01:35.710280-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.37, interface 172.17.254.93 adjacency established\n2013-07-21T09:01:38.494107-07:00 a2-magnesium Rib: %PIM-5-NBRCHG: neighbor 172.17.254.94 DOWN on interface vlan3915\n2013-07-21T09:01:44.890557-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.46, interface 172.17.254.154 adjacency established\n2013-07-21T09:01:47.753657-07:00 a2-magnesium Stp: 549: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port PeerEthernet17.\n2013-07-21T09:01:47.753713-07:00 a2-magnesium Stp: 550: %SPANTREE-6-INTERFACE_ADD: Interface PeerEthernet17 has been added to instance Vl3908\n2013-07-21T09:01:47.753732-07:00 a2-magnesium Stp: 551: %SPANTREE-6-LOOPGUARD_CONFIG_CHANGE: Loop guard enabled on port PeerEthernet17.\n2013-07-21T09:01:47.753749-07:00 a2-magnesium Stp: 552: %SPANTREE-6-INTERFACE_ADD: Interface PeerEthernet17 has been added to instance Vl3923\n2013-07-21T09:01:53.822023-07:00 a2-magnesium Rib: %PIM-5-NBRCHG: neighbor 172.17.254.94 UP on interface vlan3915\n2013-08-27T08:25:26.828785-07:00 a2-magnesium Xmpp: 553: %XMPP-6-CLIENT_DISCONNECTED: Connection to 172.22.22.17:5222 closed\n2013-08-27T17:58:05.734732-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_TERMINATED: 'Xmpp' (PID=1795) has terminated.\n2013-08-27T17:58:05.735936-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_RESTART: Restarting 'Xmpp' immediately (it had PID=1795)\n2013-08-27T17:58:05.744823-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_STARTED: 'Xmpp' starting with PID=11189 (PPID=1713) -- execing '/usr/bin/Xmpp'\n2013-08-27T18:20:43.895842-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_TERMINATED: 'Xmpp' (PID=11189) has terminated.\n2013-08-27T18:20:43.896904-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_RESTART: Restarting 'Xmpp' immediately (it had PID=11189)\n2013-08-27T18:20:43.902427-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_STARTED: 'Xmpp' starting with PID=15426 (PPID=1713) -- execing '/usr/bin/Xmpp'\n2013-08-27T18:26:13.867348-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_TERMINATED: 'Xmpp' (PID=15426) has terminated.\n2013-08-27T18:26:13.867982-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_RESTART: Restarting 'Xmpp' immediately (it had PID=15426)\n2013-08-27T18:26:13.873323-07:00 a2-magnesium ProcMgr-worker: %PROCMGR-6-PROCESS_STARTED: 'Xmpp' starting with PID=16485 (PPID=1713) -- execing '/usr/bin/Xmpp'" };

var syslogErrorMessages = { output: "2013-07-17T13:38:56.637197-07:00 a2-magnesium Aaa: 367: %AAA-4-AUTHZ_FALLBACK: Authorization method 'group radius' is currently unavailable; falling back to next method for action 'exec'.\n2013-07-21T03:00:08.602347-07:00 a2-magnesium PortSec: 407: %ETH-4-HOST_FLAPPING: Host 00:1c:73:0c:4e:1d in VLAN 3908 is flapping between interface Port-Channel1 and interface Ethernet18\n2013-07-21T03:00:16.717248-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0022 on vlan3901 to DOWN: hold timer expired\n2013-07-21T03:00:17.873829-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0050 on vlan3931 to DOWN: hold timer expired\n2013-07-21T03:00:18.741411-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0049 on vlan3930 to DOWN: hold timer expired\n2013-07-21T03:00:20.990760-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0022 on vlan3901 to UP\n2013-07-21T03:00:21.028580-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0050 on vlan3931 to UP\n2013-07-21T03:00:21.028929-07:00 a2-magnesium Rib: %ISIS-4-ISIS_ADJCHG: Neighbor State Change for SystemID 1720.2600.0049 on vlan3930 to UP\n2013-07-21T03:00:40.797020-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.37, interface 172.17.254.93 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T03:00:42.869748-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.46, interface 172.17.254.154 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T03:01:34.889973-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.46, interface 172.17.254.154 adjacency established\n2013-07-21T03:01:35.706941-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.37, interface 172.17.254.93 adjacency established\n2013-07-21T09:00:12.516555-07:00 a2-magnesium PortSec: 514: %ETH-4-HOST_FLAPPING: Host 00:1c:73:0c:55:d9 in VLAN 3908 is flapping between interface Port-Channel1 and interface Ethernet18 (message repeated 34 times in 21603.9 secs)\n2013-07-21T09:00:17.771166-07:00 a2-magnesium PortSec: 522: %ETH-4-HOST_FLAPPING: Host 00:1c:73:0c:55:d9 in VLAN 3908 is flapping between interface Ethernet18 and interface Port-Channel1 (message repeated 10 times in 5.25433 secs)\n2013-07-21T09:00:38.637184-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.46, interface 172.17.254.154 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T09:00:44.169278-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_TEARDOWN: NGB 172.26.0.37, interface 172.17.254.93 adjacency dropped: inactivity timer expired, state was: FULL\n2013-07-21T09:01:35.710280-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.37, interface 172.17.254.93 adjacency established\n2013-07-21T09:01:44.890557-07:00 a2-magnesium Rib: %OSPF-4-OSPF_ADJACENCY_ESTABLISHED: NGB 172.26.0.46, interface 172.17.254.154 adjacency established" };

//# sourceURL=mockApp.js
