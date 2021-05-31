import json
import os
import datetime
import time
import dateutil.parser
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.settings import api_settings
from rest_framework.exceptions import ParseError, NotFound, PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from agalaxy_share.licensing.exceptions import LicenseLimitError
from agalaxy_share.axapi.utils import extract_response_message
from agalaxy_share.utility import scheduler_utility
from agalaxy_event_amqp.event_factory import EventFactory
from agalaxy_event_amqp.event_alert_factory import EventAlertFactory
from agalaxy_event_alert.event_alert_configuration import AlertSourceType, AlertSeverity
from agalaxy_sdk.DeviceApi import device_api
from agalaxy_sdk.Device_groupApi import device_group_api
from agalaxy_sdk.Tps_settingsApi import tps_settings_api
from agalaxy_tps.tps_utility import validate_uuid4
from tps2.settings import tps2_logger
from common.exceptions import DeviceConfigurationError
from common.mixins import TotalCountMixin, TpsESLoggerMixin
from common.axapi.shim import AXAPIService
from common.views import TpsModelViewSet
from common.utils import lookup_device_ip_from_id, lookup_device_group_name_from_id
from ddos.zone.models import DdosDstZone, DDOSZoneEscalation
from ddos.zone.serializers import DdosDstZoneSerializer, DDOSZoneEscalationSerializer
from ddos.zone.incident.models import ZoneIncident
from ddos.zone.api import DdosDstZoneApi, ZoneAPI
from ddos.zone.mitigation.models import ZoneMitigationConfig, ZoneServiceMitigationConfig
from ddos.zone.mitigation.api import ZoneMitigationAPI
from ddos.zone.api import TpsDeviceZoneTemplateCollector
from ddos.zone.mixins import ZoneActionMixin
from agalaxy_share.restful_api.clients import TPS2RESTClient
from agalaxy_share.tps2.notification_template import NOTIFY_USERNAME, NOTIFY_PASSWORD


class DdosDstZoneViewSet(TpsModelViewSet, TotalCountMixin):
    queryset = DdosDstZone.objects.all()
    serializer_class = DdosDstZoneSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'options']
    filter_fields = ('name', 'status')
    # Since "config" field includes too many information, which causes many unexpected search result,
    # remove it from the list of search_fields temporarily.
    search_fields = ['name', 'status', 'device_group', 'detector__id']
    ordering_fields = ['name', 'status', 'created', 'modified']

    def get_queryset(self):
        """Override to check for special `has_detector` filter"""
        queryset = super(DdosDstZoneViewSet, self).get_queryset()
        if 'zone_name' in self.request.query_params:
            queryset = queryset.filter(name=self.request.query_params['zone_name'])
        if 'has_detector' in self.request.query_params:
            if self.request.query_params['has_detector'] in ['1', 'true', 'True']:
                queryset = queryset.filter(detector__isnull=False)
            else:
                queryset = queryset.filter(detector__isnull=True)

        # (echou): Adding device_group to filter_fields did not work, possibly due to older version of django_filters
        # not support UUIDField
        if 'device_group' in self.request.query_params:
            if not validate_uuid4(self.request.query_params['device_group']):
                raise serializers.ValidationError({'device_group': 'Device group filter value is invalid.'})
            queryset = queryset.filter(device_group=self.request.query_params['device_group'])

        if 'detector_id' in self.request.query_params:
            if not validate_uuid4(self.request.query_params['detector_id']):
                raise serializers.ValidationError({'detector_id': 'Detector ID filter value is invalid.'})
            queryset = queryset.filter(detector_id=self.request.query_params['detector_id'])

        # Special case for ordering by zone_name
        if 'ordering' in self.request.query_params:
            if self.request.query_params['ordering'] == 'zone_name':
                queryset = queryset.order_by('name')
            if self.request.query_params['ordering'] == '-zone_name':
                queryset = queryset.order_by('-name')
        return queryset

    def create(self, request, *args, **kwargs):

        response = super(DdosDstZoneViewSet, self).create(request)
        es_logger = self.get_es_logger(request)
        if response.status_code == 201:
            try:
                obj = DdosDstZone.objects.get(name=request.data['zone_name'])
            except:
                raise serializers.ValidationError("Zone %s does not exist" % request.data['zone_name'])

            if obj.device_group or obj.detector:
                zone_api = DdosDstZoneApi(instance=obj)
                try:
                    # (echou): Use new ZoneAPI to push
                    new_zone_api = ZoneAPI(obj)
                    new_zone_api.push_support_objects()
                    zone_api.configure_zone()
                except Exception as exc:
                    msg = 'Failed to push zone %s to TPS device(s).' % obj.name
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    obj.delete()  # rollback object
                    raise exc

            es_logger.info('Zone {} created successfully'.format(obj.name))
        else:
            es_logger.error('Failed to create zone.')
        return response

    def update(self, request, *args, **kwargs):
        # Check if the detector_id has changed
        obj = self.get_object()
        detector_id = request.data.get('detector_id')
        obj_config = json.loads(obj.config)
        original_uuid_dict = obj_config.get('uuid_dict', {})

        update_detector = False
        original_detector_id = None

        if obj.detector and str(obj.detector.id) != detector_id:
            original_detector_id = str(obj.detector.id)
            update_detector = True
        # If detector ID is in payload, but zone did not have detector before (i.e. add detector device)
        elif detector_id and not obj.detector:
            update_detector = True

        # Check if there are ongoing zone service incidents
        if obj.status == DdosDstZone.STATUS_MITIGATION:
            queryset = ZoneIncident.objects.filter(zone=obj.name)
            queryset = ZoneIncident.filter_active(queryset)
            conflict = False
            if queryset.count():
                service_key_list = []
                # Check if services removed conflict with ongoing incident
                for el in request.data.get('port', {}).get('zone_service_list', []):
                    service_key_list.append('{}+{}'.format(el['port'], el['protocol']))
                for el in request.data.get('port', {}).get('zone_service_other_list', []):
                    service_key_list.append('{}+{}'.format(el['port_other'], el['protocol']))
                for el in request.data.get('port_range_list', []):
                    service_key_list.append(
                        '{}+{}+{}'.format(el['port_range_start'], el['port_range_end'], el['protocol']))
                for el in request.data.get('ip_proto_list', []):
                    service_key_list.append('ip-proto+{}'.format(el['protocol']))
                for inc in queryset:
                    if inc.service not in service_key_list:
                        tps2_logger.info('Zone Incident {} for zone {} service {} conflicts with zone update'.format(
                            inc.id, obj.name, inc.service))
                        tps2_logger.info('Zone update service keys: {}'.format(service_key_list))
                        conflict = True
                        break
            if conflict:
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: 'Cannot remove service(s) due to ongoing incident.'})

        # Check if the IP list has changed
        instance_ip_set = set(obj_config.get('ip_list', []))
        data_ip_set = set(request.data.get('ip_list', []))
        if instance_ip_set == data_ip_set:
            ip_list_changed = False
            ip_list_removed = []
        else:
            ip_list_changed = True
            ip_list_removed = list(instance_ip_set - data_ip_set)

        # Check if unset device group
        if not request.data.get('device_group') and obj.device_group:
            if obj.status != DdosDstZone.STATUS_NORMAL:
                return Response(
                    status=409,
                    data={
                        'code': 409,
                        'message': 'Cannot unset mitigation device group when Zone status is {}.'.format(obj.status)
                    }
                )
            unset_device_group_id = str(obj.device_group)
        # Check if changed device group
        elif obj.device_group:
            if str(obj.device_group) != request.data.get('device_group'):
                unset_device_group_id = str(obj.device_group)
            else:
                unset_device_group_id = None
        else:
            unset_device_group_id = None

        response = super(DdosDstZoneViewSet, self).update(request)

        # Re-fetch object to get changes
        obj = self.get_object()
        es_logger = self.get_es_logger(request, uuid=str(obj.id))
        if response.status_code == 200:
            if unset_device_group_id:
                # Check if the device group is stale
                try:
                    device_group_api.get_device_group_by_id(unset_device_group_id)
                except Exception as exc:
                    tps2_logger.exception('Failed to lookup device group %s: %s', unset_device_group_id, exc.message)
                    obj.device_group = None
                    obj.save()
                    msg = 'Device group {} no longer valid. Removing from zone {}.'.format(
                        unset_device_group_id, obj.name)
                    tps2_logger.warning(msg)
                    es_logger.warning(msg)
                    return response

                # Find the devices no longer in the mitigator group and delete zone
                # from those device only
                new_device_ids = ZoneAPI.get_device_ids_from_device_group(request.data.get('device_group'))
                old_device_ids = ZoneAPI.get_device_ids_from_device_group(unset_device_group_id)
                unset_device_id_list = list(set(old_device_ids) - set(new_device_ids))

                device_results = AXAPIService.send_to_device_list(
                    device_id_list=unset_device_id_list,
                    request_list=[{
                        'resource': '/ddos/dst/zone/{}'.format(obj.name),
                        'method': 'DELETE'
                    }],
                    stop_on_error=False)
                device_errors = {}
                for device_id, result in device_results.iteritems():
                    if result.get('error_indices'):
                        error_messages = []
                        for idx in result['error_indices']:
                            r = result['response_list'][idx]
                            error_messages.append(extract_response_message(r['text']))
                        device_errors[device_id] = error_messages

                error_list = []
                if device_errors:
                    msg = "Failed to delete zone {} on TPS device(s). ".format(obj.name)
                    for device_id, error_messages in device_errors.iteritems():
                        # Try to lookup device IP, fallback on device ID
                        try:
                            res = device_api.get_device_by_id(device_id)
                            device_ip = res.mgmt_ip_address
                        except:
                            tps2_logger.exception('Failed to lookup device IP from ID {}'.format(device_id))
                            device_ip = device_id
                        error_list.append(msg + "Device {}: {}. ".format(device_ip, ", ".join(error_messages)))

                # Remove BGP on old devices, and configure BGP on new devices
                if obj.status != DdosDstZone.STATUS_NORMAL:
                    new_device_ids = ZoneAPI.get_device_ids_from_device_group(str(obj.device_group))
                    old_device_ids = ZoneAPI.get_device_ids_from_device_group(unset_device_group_id)

                    # Minimize aXAPI calls by finding the minimal sets
                    set_device_id_list = list(set(new_device_ids) - set(old_device_ids))
                    unset_device_id_list = list(set(old_device_ids) - set(new_device_ids))
                    ip_list = json.loads(obj.config).get('ip_list', [])

                    if unset_device_id_list:
                        try:
                            ZoneAPI.remove_bgp_on_devices(device_id_list=unset_device_id_list, ip_list=ip_list)
                        except Exception as exc:
                            msg = 'Failed to remove BGP on devices. Error: {}. Device IDs: {}, IP list: {}.'.format(
                                exc.message,
                                ", ".join(unset_device_id_list),
                                ", ".join(ip_list)
                            )
                            tps2_logger.exception(msg)
                            error_list.append("Failed to remove BGP configuration: {}.".format(exc.message))

                    if set_device_id_list:
                        try:
                            ZoneAPI.configure_bgp_on_devices(device_id_list=set_device_id_list, ip_list=ip_list)
                        except Exception as exc:
                            msg = 'Failed to configure BGP on devices. Error: {}. Device IDs: {}, IP list: {}.'.format(
                                exc.message,
                                ", ".join(set_device_id_list),
                                ", ".join(ip_list)
                            )
                            tps2_logger.exception(msg)
                            error_list.append("Failed to set BGP configuration: {}.".format(exc.message))

                if error_list:
                    msg = 'Zone {} updated but with errors: {}.'.format(obj.name, " ".join(error_list))
                    tps2_logger.error(msg)
                    es_logger.error(msg)
                    raise DeviceConfigurationError(" ".join(error_list))

            if request.data.get('device_group'):
                zone_id = kwargs['pk']
                zone_api = DdosDstZoneApi(object_id=zone_id)
                new_api = ZoneAPI(zone_id)

                try:
                    new_api.push_support_objects()
                    zone_api.configure_zone(original_uuid_dict=original_uuid_dict)
                except DeviceConfigurationError as exc:
                    msg = 'Failed to update zone {} configuration on devices. Error: {}.'.format(obj.name, exc.message)
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    raise exc

                if ip_list_changed:
                    # Refetch obj from DB and get latest zone status
                    updated_obj = DdosDstZone.objects.get(id=obj.id)
                    try:
                        if updated_obj.status == DdosDstZone.STATUS_MITIGATION:
                            # Update BGP
                            if updated_obj.device_group:
                                ip_list = json.loads(updated_obj.config).get('ip_list', [])
                                device_id_list = ZoneAPI.get_device_ids_from_device_group(str(updated_obj.device_group))
                                ZoneAPI.configure_bgp_on_devices(device_id_list=device_id_list, ip_list=ip_list)
                    except Exception as exc:
                        msg = "Failed to update BGP configuration for zone {}. Error: {}.".format(
                            updated_obj.name, exc.message)
                        tps2_logger.exception(msg)
                        es_logger.error(msg)
                        raise exc
            elif update_detector or obj.detector:
                # No device group, but need to set detector
                # Set new detector
                zone_id = kwargs['pk']
                zone_api = DdosDstZoneApi(object_id=zone_id)
                try:
                    zone_api.configure_zone(original_uuid_dict=original_uuid_dict)
                except DeviceConfigurationError as exc:
                    msg = 'Failed to configure zone {} on detector device.'.format(obj.name)
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    raise exc

            # Remove zone from previous detector if needed
            if update_detector and original_detector_id:
                zone_id = kwargs['pk']
                zone_api = DdosDstZoneApi(object_id=zone_id)
                try:
                    zone_api.remove_zone_on_detector(detector_id=original_detector_id)
                except DeviceConfigurationError as exc:
                    msg = 'Failed to remove zone {} from previous detector device.'.format(obj.name)
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    raise exc

        msg = "Zone {} updated successfully.".format(obj.name)
        tps2_logger.info(msg)
        es_logger.info(msg)
        return response

    def destroy(self, request, *args, **kwargs):
        obj = DdosDstZone.objects.get(pk=kwargs['pk'])
        zone_name = obj.name
        # Check for zone status
        if obj.status != DdosDstZone.STATUS_NORMAL:
            if request.REQUEST.get('force_delete', '') in ['1', 'true', 'True']:
                # Force delete, so stop all the incidents
                ZoneIncident.objects.filter(zone=zone_name).update(status=ZoneIncident.STATUS_STOPPED)
            else:
                return Response(
                    status=400,
                    data={
                        'code': 400,
                        'message': 'Unable to delete zone because it is in {} status.'.format(obj.status)
                    }
                )
        zone_id = kwargs['pk']
        error_message = None
        es_logger = self.get_es_logger(request, uuid=zone_id)
        try:
            zone_api = DdosDstZoneApi(object_id=zone_id)
            force_delete = True if request.REQUEST.get('force_delete', '') in ['1', 'true', 'True'] else False
            zone_api.clear_zone(force_delete=force_delete)
        except Exception as exc:
            tps2_logger.exception('Exception when trying to clear zone %s: %s', zone_name, exc.message)
            error_message = exc.message

        obj.delete()
        if error_message:
            msg = "Zone {} deleted but with error: {}.".format(zone_name, error_message)
            tps2_logger.error(msg)
            es_logger.error(msg)
        else:
            msg = "Zone {} deleted successfully.".format(zone_name)
            tps2_logger.info(msg)
            es_logger.info(msg)

        # Publish event for deleting zone
        EventFactory.publish(
            "a10.agalaxy.tps.ddos.zone.deleted",
            source_ip='127.0.0.1',
            source_component="TPS",
            description="DDOS zone deleted",
            event_data={
                'zone_id': zone_id,
                'zone_name': zone_name
            }
        )
        if error_message:
            return Response(status=202, data={'code': 202, 'message': 'Zone deleted with errors: %s.' % error_message})
        else:
            return Response(status=204)


class ZoneServiceListView(APIView):

    def get(self, request, *args, **kwargs):
        zone_id = self.kwargs.get('zone_id')
        zone_api = DdosDstZoneApi(object_id=zone_id)
        service_list = zone_api.get_service_list()
        return Response(service_list)


class ZoneStartStopMitigationView(APIView, TpsESLoggerMixin):
    """
    Start/Stop mitigation on a zone
    """
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        return Response(status=200, data={'message': 'Send HTTP POST to {} mitigation on zone.'.format(action)})

    def post(self, request, *args, **kwargs):
        zone_id = self.kwargs.get('zone_id')
        incident_id_list = []
        if not zone_id:
            return Response(status=400, data={'code': 400, 'message': 'Zone ID is required.'})
        action = self.kwargs.get('action')
        if not action or action not in ['start', 'stop']:
            return Response(status=400, data={'code': 400, 'message': 'Invalid action'})

        try:
            zone = DdosDstZone.objects.get(id=zone_id)
        except ObjectDoesNotExist:
            return Response(status=404)

        es_logger = self.get_es_logger(request, uuid=str(zone.id))
        zone_api = ZoneAPI(zone)

        if action == 'start':
            try:
                zone_api.start_mitigation()
            except Exception as exc:
                msg = "Failed to start mitigation on zone {}. Error: {}.".format(zone.name, exc.message)
                tps2_logger.exception(msg)
                es_logger.error(msg)
                raise exc
            log_message = "Mitigation started on zone {}.".format(zone.name)
        else:
            try:
                incident_id_list = zone_api.stop_mitigation()
            except serializers.ValidationError as exc:
                tps2_logger.error("Failed to stop mitigation on zone {}. Error: {}.".format(zone.name, exc.message))
                raise exc
            except Exception as exc:
                msg = "Failed to stop mitigation on zone {}. Error: {}.".format(zone.name, exc.message)
                tps2_logger.exception(msg)
                es_logger.error(msg)
                raise exc
            log_message = "Mitigation stopped on zone {}.".format(zone.name)
        tps2_logger.info(log_message)
        es_logger.info(log_message)
        if action == 'stop':
            # Publish event
            EventFactory.publish(
                "a10.agalaxy.tps.ddos.zone.mitigation.stopped",
                source_ip='127.0.0.1',
                source_component="tps",
                description="DDOS zone mitigation stopped",
                event_data={
                    'zone_id': zone_id,
                    'zone_name': zone.name,
                    'incident_id_list': [str(inc_id) for inc_id in incident_id_list]
                }
            )
        return Response(status=200, data={'code': 200, 'message': log_message})


class ZoneDeviceGroupUpdatedView(APIView, TpsESLoggerMixin):
    """
    A callback endpoint to execute action(s) when a device group's device membership is updated.
    """
    http_method_names = ['post']

    def update_incident_uuid(self, zone_config, incident_list):
        """
        Updates the uuid dict of the active incident by extracting from the updated zone uuid dict
        """
        zone_uuid_dict = zone_config.get('uuid_dict', {})
        service_dict = {}
        for device_id, uuid_dict in zone_uuid_dict.iteritems():
            for service, data in uuid_dict.get("service", {}).iteritems():
                if service not in service_dict:
                    service_dict[service] = {"indicator": {}, "general": {}}

                indicator_uuid = data.get("indicator")
                if indicator_uuid:
                    service_dict[service]["indicator"].update({device_id: indicator_uuid})

                general_uuid = data.get("general")
                if general_uuid:
                    service_dict[service]["general"].update({device_id: general_uuid})

        for incident in incident_list:
            if incident.status in ZoneIncident.ACTIVE_STATUSES and incident.service in service_dict:
                config = json.loads(incident.config)
                if "uuid_dict" not in config:
                    config["uuid_dict"] = {"general": {}, "indicator": {}}
                if "general" not in config["uuid_dict"]:
                    config["uuid_dict"]["general"] = {}
                if "indicator" not in config["uuid_dict"]:
                    config["uuid_dict"]["indicator"] = {}

                # update the uuid for the existing device and new device
                # uuid is not removed for the non-existent device (to preserve reference for the chart data history)
                if service_dict[incident.service].get("general"):
                    config["uuid_dict"]["general"].update(service_dict[incident.service]["general"])
                if service_dict[incident.service].get("indicator"):
                    config["uuid_dict"]["indicator"].update(service_dict[incident.service]["indicator"])
                incident.config = json.dumps(config)
                incident.save()

    def update_zone_uuid(self, zone, device_group_id):
        """
        Updates zone uuid dict by getting sending a GET axapi request to each device in device group
        """
        svc = AXAPIService(device_group_id=device_group_id)
        request_list = [{
            'method': 'GET',
            'resource': '/ddos/dst/zone/%s' % zone.name
        }]
        result = svc.send_to_device_group(request_list=request_list, stop_on_error=False)
        uuid_dict = {}
        for device_id, result_data in result.iteritems():
            if result_data.get('response_list'):
                zone_config = json.loads(result_data['response_list'][0]['text'])
                zone_uuid_dict = DdosDstZoneApi.extract_uuid(zone_config)
                uuid_dict[device_id] = zone_uuid_dict

        config = json.loads(zone.config)
        # Save local configuration
        config['uuid_dict'] = uuid_dict
        zone.config = json.dumps(config)
        zone.save()

    def post(self, request, *args, **kwargs):
        device_group_id = request.data.get('device_group_id', None)
        device_ids_added = request.data.get('device_ids_added', [])
        device_ids_removed = request.data.get('device_ids_removed', [])
        if not device_group_id:
            return Response(status=400, data={'code': 400, 'message': 'Device group ID is required.'})
        if not device_ids_added and not device_ids_removed:
            return Response(
                status=400, data={'code': 400, 'message': 'Must specify device_ids_added or device_id_removed.'})
        # Get a list of zones that need to be updated
        zone_list = DdosDstZone.objects.filter(device_group=device_group_id)
        if not zone_list.count():
            return Response(
                status=200,
                data={'code': 200, 'message': 'No zones found for device group {}'.format(device_group_id)}
            )
        error_list = []
        es_logger = self.get_es_logger(request)
        device_group_name = lookup_device_group_name_from_id(device_group_id)
        device_ips_added = []
        device_ips_removed = []
        for device_id in device_ids_added:
            device_ips_added.append(lookup_device_ip_from_id(device_id))
        for device_id in device_ids_removed:
            device_ips_removed.append(lookup_device_ip_from_id(device_id))

        for zone in zone_list:
            # Get the list of active incident to update uuid dicts
            incident_list = ZoneIncident.objects.filter(zone=zone.name)
            incident_list = ZoneIncident.filter_active(incident_list)

            # Remove BGP config and delete zone on removed device
            if device_ids_removed:
                try:
                    if zone.status == DdosDstZone.STATUS_MITIGATION:
                        ip_list = json.loads(zone.config).get('ip_list', [])
                        ZoneAPI.remove_bgp_on_devices(device_id_list=device_ids_removed, ip_list=ip_list)
                    ZoneAPI.delete_zone_on_device_list(instance=zone, device_id_list=device_ids_removed)

                    # Remove removed device uuid dict from the zone
                    config = json.loads(zone.config)
                    uuid_dict = config.get("uuid_dict")
                    if uuid_dict:
                        for device_id in device_ids_removed:
                            if device_id in uuid_dict:
                                del uuid_dict[device_id]
                        config['uuid_dict'] = uuid_dict
                        zone.config = json.dumps(config)
                        zone.save()

                except Exception as exc:
                    msg = 'Failed to clean up zone {0} on removed devices {1}. Error: {2}.'.format(
                        zone.name, ", ".join(device_ips_removed), exc.message)
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    error_list.append(msg)
                    # Put zone in error status
                    zone.status = DdosDstZone.STATUS_ERROR
                    zone.save()
                    continue

            # If zone has a detector, re-balance the indicator thresholds
            if zone.detector:
                try:
                    # Re-balance threshold values by re-configuring zone
                    new_api = ZoneAPI(zone)
                    new_api.push_support_objects()
                    old_api = DdosDstZoneApi(instance=zone)
                    old_api.configure_zone()
                except Exception as exc:
                    msg = 'Failed to configure zone {}. Error: {}.'.format(zone.name, exc.message)
                    tps2_logger.exception(msg)
                    es_logger.error(msg)
                    error_list.append(msg)
                    # Put zone in error status
                    zone.status = DdosDstZone.STATUS_ERROR
                    zone.save()
                    continue

            # Push configuration to new devices
            if device_ids_added:
                # Note: only push zone configuration if no detector, otherwise already pushed above
                if not zone.detector:
                    try:
                        ZoneAPI.push_zone_to_device_list(instance=zone, device_id_list=device_ids_added)

                        # Update the uuid dict in the zone
                        self.update_zone_uuid(zone, device_group_id)

                        # Update incident uuid dict
                        zone_config = json.loads(zone.config)
                        self.update_incident_uuid(zone_config, incident_list)

                    except Exception as exc:
                        msg = 'Failed to push zone {0} to new devices {1}. Error: {2}.'.format(
                            zone.name, ", ".join(device_ips_added), exc.message)
                        tps2_logger.exception(msg)
                        es_logger.error(msg)
                        error_list.append(msg)
                        # Put zone in error status
                        zone.status = DdosDstZone.STATUS_ERROR
                        zone.save()
                        continue

                # If zone is under mitigation, push countermeasures and BGP to the added devices
                if zone.status == DdosDstZone.STATUS_MITIGATION:
                    # Push countermeasures
                    try:
                        zone_mitigation_api = ZoneMitigationAPI(zone)
                        # Push countermeasures if enabled
                        zmc_queryset = ZoneMitigationConfig.objects.filter(zone=zone, enabled=True)
                        if zmc_queryset.count() == 1:  # There should only be one enabled
                            zone_mitigation_api.push_zone_mitigation_config()

                        # Push zone service countermeasures that are enabled for active incidents
                        for incident in incident_list:
                            qs = ZoneServiceMitigationConfig.objects.filter(incident=incident, enabled=True)
                            if qs.count() == 1:  # There should only be 1 enabled per incident
                                zone_mitigation_api.push_zone_service_mitigation_config(
                                    zone_incident=incident)
                    except Exception as exc:
                        msg = 'Failed to configure countermeasures for zone {}. Error: {}.'.format(
                            zone.name, exc.message)
                        tps2_logger.exception(msg)
                        es_logger.error(msg)
                        error_list.append(msg)
                        # Put zone in error status
                        zone.status = DdosDstZone.STATUS_ERROR
                        zone.save()
                        continue
                    # Push BGP
                    try:
                        ip_list = json.loads(zone.config).get('ip_list', [])
                        ZoneAPI.configure_bgp_on_devices(device_id_list=device_ids_added, ip_list=ip_list)
                    except Exception as exc:
                        msg = 'Failed to configure BGP for zone {}. Error: {}.'.format(zone.name, exc.message)
                        tps2_logger.exception(msg)
                        es_logger.error(msg)
                        error_list.append(msg)
                        # Put zone in error status
                        zone.status = DdosDstZone.STATUS_ERROR
                        zone.save()
                        continue

        # Check for errors
        if error_list:
            msg = "Errors were encountered when processing device group {} update.".format(device_group_name)
            if device_ips_added:
                msg += " Devices added: {}.".format(", ".join(device_ips_added))
            if device_ips_removed:
                msg += " Devices removed: {}.".format(", ".join(device_ips_removed))
            msg += " Errors: {}.".format(". ".join(error_list))
            tps2_logger.error(msg)
            es_logger.error(msg)
            return Response(
                status=500,
                data={
                    'code': 500,
                    'message': 'Failed to update zones for device group {} updated event. '
                               'Errors: {}'.format(device_group_name, ', '.join(error_list))
                }
            )

        msg = "Device group {} update event processed successfully.".format(device_group_name)
        if device_ips_added:
            msg += " Devices added: {}.".format(", ".join(device_ips_added))
        if device_ips_removed:
            msg += " Devices removed: {}.".format(", ".join(device_ips_removed))
        tps2_logger.info(msg)
        es_logger.info(msg)
        return Response(status=200, data={'code': 200, 'message': 'Zones updated successfully on devices.'})


class ZoneDeviceGroupDeletedView(APIView, TpsESLoggerMixin):
    """
    A callback endpoint to execute action(s) when a device group is deleted.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        device_group_id = request.data.get('device_group_id', None)
        device_id_list = request.data.get('device_ids', [])
        if not device_group_id:
            return Response(status=400, data={'code': 400, 'message': 'Device group ID is required.'})
        # Get a list of zones that need to be updated
        zone_list = DdosDstZone.objects.filter(device_group=device_group_id)
        if not zone_list.count():
            return Response(
                status=200,
                data={'code': 200, 'message': 'No zones found for device group {}'.format(device_group_id)}
            )
        device_group_name = lookup_device_group_name_from_id(device_group_id)
        device_ip_list = []
        for device_id in device_id_list:
            device_ip_list.append(lookup_device_ip_from_id(device_id))
        es_logger = self.get_es_logger(request)
        error_list = []
        zone_name_list = [zone.name for zone in zone_list]
        zone_error_names = []
        for zone in zone_list:
            # Remove device group on zone
            zone.device_group = None
            zone.save()

            # Remove zone from device
            if device_ip_list:
                try:
                    ZoneAPI.delete_zone_on_device_list(instance=zone, device_id_list=device_id_list)

                    # Remove removed device uuid dict from the zone
                    config = json.loads(zone.config)
                    uuid_dict = config.get("uuid_dict")
                    if uuid_dict:
                        for device_id in device_id_list:
                            if device_id in uuid_dict:
                                del uuid_dict[device_id]
                        config['uuid_dict'] = uuid_dict
                        zone.config = json.dumps(config)
                        zone.save()

                except Exception as exc:
                    error_list.append(exc.message)
                    zone_error_names.append(zone.name)

        # Check for errors and log them
        if error_list:
            msg = "Errors encountered when processsing device group {} deleted event.".format(device_group_name)
            msg += " Devices: {}.".format(", ".join(device_ip_list))
            msg += " Zones processed: {}.".format(", ".join(zone_name_list))
            msg += " Zones with errors: {}.".format(", ".join(zone_error_names))
            msg += " Errors: {}.".format(". ".join(error_list))
            tps2_logger.error(msg)
            es_logger.error(msg)
        else:
            msg = "Device group {} delete event processed.".format(device_group_name)
            if device_ip_list:
                msg += " Devices: {}.".format(", ".join(device_ip_list))
            msg += " Zones processed: {}.".format(", ".join(zone_name_list))
            tps2_logger.info(msg)
            es_logger.info(msg)
        return Response(status=200, data={'code': 200, 'message': 'Zones updated.'})


class ZoneDeviceScanView(APIView):
    """
    A callback endpoint to get zone objects from a device.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        device_id = request.data.get('device_id', None)
        if not device_id:
            return Response(status=400, data={'code': 400, 'message': 'Device ID is required.'})
        zone_collector = TpsDeviceZoneTemplateCollector(device_id=device_id)
        error_list = zone_collector.collect_zone_and_support_objects()

        if error_list:
            return Response(
                status=400,
                data={
                    'code': 400,
                    'message': 'Errors occur during zone collection on device {}. '
                               'Errors: {}'.format(device_id, ', '.join(error_list))
                }
            )

        return Response(status=200, data={'code': 200, 'message': 'Zones collected successfully on device.'})


class ZoneEscalationView(ListCreateAPIView, TpsESLoggerMixin):
    """Handles DDOS zone escalations and de-escalations. Called by the event handler for DDOS notifications from TPS."""
    queryset = DDOSZoneEscalation.objects.all()
    serializer_class = DDOSZoneEscalationSerializer
    filter_fields = ('device_id', 'host_id', 'zone_name', 'event_type')

    def get_queryset(self):
        queryset = super(ZoneEscalationView, self).get_queryset()
        zone_id = self.kwargs.get('zone_id', None)
        service = self.kwargs.get('service', None)
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        if service:
            queryset = queryset.filter(service=service)
        if 'incident_id' in self.request.query_params:
            queryset = queryset.filter(incident_id=self.request.query_params['incident_id'])
        if 'start' in self.request.query_params:
            try:
                start_dt = dateutil.parser.parse(self.request.query_params['start'])
            except:
                return Response(
                    status=400,
                    data={
                        'code': 400,
                        'message': 'Failed to parse start. Please make sure it is the UTC time in ISO format'
                    }
                )
            queryset = queryset.filter(created__gte=start_dt)
        if 'end' in self.request.query_params:
            try:
                end_dt = dateutil.parser.parse(self.request.query_params['end'])
            except:
                return Response(
                    status=400,
                    data={
                        'code': 400,
                        'message': 'Failed to parse end. Please make sure it is the UTC time in ISO format'
                    }
                )
            queryset = queryset.filter(created__lte=end_dt)
        return queryset

    def post(self, request, *args, **kwargs):
        # Check the payload for internal auth credentials
        payload = json.loads(request.body)
        username = payload.get('user_name', '')
        password = payload.get('password', '')
        if username != NOTIFY_USERNAME or password != NOTIFY_PASSWORD:  # note: NOTIFY_PASSWORD is encrypted
            raise PermissionDenied

        # Call super to write the event to db
        response = super(ZoneEscalationView, self).post(request, *args, **kwargs)
        if response.status_code not in [200, 201]:
            # If not success, return early
            return response

        # Check if need to adjust incident level and/or auto-stop mitigation
        obj = DDOSZoneEscalation.objects.get(id=response.data['id'])
        zone = DdosDstZone.objects.get(id=obj.zone_id)
        device_id_list = ZoneAPI.get_device_ids_from_device_group(str(zone.device_group))
        zone_es_logger = self.get_es_logger(request, uuid=str(zone.id))
        # Find incident
        queryset = ZoneIncident.objects.filter(zone=obj.zone_name, service=obj.service)
        queryset = ZoneIncident.filter_active(queryset)
        if queryset.count() not in [0, 1]:
            err_msg = 'Multiple active zone incidents for zone {} service {}'.format(obj.zone_name, obj.service)
            tps2_logger.error(err_msg)
            return Response(
                status=202,
                data={
                    'code': 202,
                    'message': 'DDOS escalation/de-escalation event saved but with error: {}'.format(err_msg)
                }
            )
        if queryset.count() == 1:
            # Incident found. Check if need to increment/decrement escalation level.
            incident = queryset[0]
            incident_es_logger = self.get_es_logger(request, uuid=str(incident.id))
            tps2_logger.info('DDOS escalation/de-escalation event found one incident %s', incident.name)
            if incident.config:
                changed_level = None
                inc_cfg = json.loads(incident.config)
                if inc_cfg.get('level'):
                    inc_lvl = int(inc_cfg['level'])
                    if obj.level > inc_lvl:
                        # Escalation
                        changed_level = obj.level
                        inc_cfg['level'] = str(obj.level)
                        incident.config = json.dumps(inc_cfg)
                        incident.save()
                        # Check for level 5, i.e. manual-mode
                        if obj.level == 5:
                            msg = 'Incident {} is in manual mode'.format(incident.name)
                        else:
                            msg = 'Incident escalation: {} is now at level {}.'.format(incident.name, obj.level)
                        tps2_logger.info(msg)
                        incident_es_logger.info(msg)
                    elif obj.level < inc_lvl:
                        # Find all saved levels from other devices
                        highest_level = obj.level
                        queryset = DDOSZoneEscalation.objects.filter(incident_id=incident.id)
                        for device_id in device_id_list:
                            if device_id != str(obj.device_id):  # Do not include this event's device
                                try:
                                    latest = queryset.filter(device_id=device_id).latest('created')
                                    if latest.level > obj.level:
                                        highest_level = latest.level
                                        break  # no de-escalation because at least one device is higher level
                                except ObjectDoesNotExist:
                                    pass
                        if highest_level <= obj.level:
                            # De-escalate
                            inc_cfg['level'] = str(obj.level)
                            incident.config = json.dumps(inc_cfg)
                            incident.save()
                            # Check for level 5, i.e. manual-mode
                            if obj.level == 5:
                                msg = 'Incident {} is in manual mode'.format(incident.name)
                            else:
                                msg = 'Incident de-escalation: {} is now at level {}.'.format(incident.name, obj.level)
                            tps2_logger.info(msg)
                            incident_es_logger.info(msg)
                            changed_level = obj.level

                    if changed_level is not None:
                        # Check if changed level is zero and stop the zone incident
                        if changed_level == 0:
                            try:
                                api_client = TPS2RESTClient()
                                res = api_client.post('/ddos/zone/incident/{}/stop/'.format(str(incident.id)))
                                if res.status_code != 200:
                                    try:
                                        res_data = res.json()
                                        msg = 'Failed to stop zone incident {}. {}'.format(
                                            incident.name, res_data['message'])
                                    except:
                                        msg = "Failed to stop zone incident %s." % incident.name
                                    tps2_logger.error(msg)
                                    zone_es_logger.error(msg)
                                zone_es_logger.info('Incident %s is stopped.' % incident.name)
                            except Exception as exc:
                                tps2_logger.exception('Failed to stop zone incident %s. Error: %s.' % (
                                    incident.name, exc.message))
                                zone_es_logger.error('Failed to stop zone incident %s.' % incident.name)
                        else:
                            # Publish incident change event
                            try:
                                zone_obj = DdosDstZone.objects.get(name=incident.zone)
                                zone_id = str(zone_obj.id)
                            except Exception as exc:
                                tps2_logger.exception('Failed to lookup zone by name %s: %s', incident.zone, exc.message)
                                zone_id = None
                            incident_event_data = {
                                "incident_id": str(incident.id),
                                "incident_name": incident.name,
                                "zone_id": zone_id,
                                "zone_name": incident.zone,
                                "service": incident.service,
                                "status": incident.status,
                                "level": changed_level
                            }
                            EventFactory.publish(
                                "a10.agalaxy.tps.ddos.zone.incident.notify",
                                source_ip='127.0.0.1',
                                source_component="tps",
                                description="DDOS zone incident notify",
                                event_data=incident_event_data
                            )

        # Check System auto stop mitigation flag
        auto_stop = False
        try:
            res = tps_settings_api.get_tps_settings()
            auto_stop = res.auto_stop_zone_mitigation
        except:
            tps2_logger.exception("Failed to get System TPS settings")

        # Check for auto-stop mitigation conditions
        if auto_stop and obj.level == 0 and zone.status == DdosDstZone.STATUS_MITIGATION:
            # Get all active incidents for the zone
            queryset = ZoneIncident.objects.filter(zone=zone.name)
            queryset = ZoneIncident.filter_active(queryset)
            all_level_zero = True
            for inc in queryset:
                if inc.config:
                    inc_cfg = json.loads(inc.config)
                    if inc_cfg.get('level') and int(inc_cfg['level']) > 0:
                        all_level_zero = False
                        break  # at least one incident has level > 0, break out early

            if all_level_zero:
                msg = 'All incidents for zone {} have returned to level 0.'.format(zone.name)
                try:
                    # Stop mitigation
                    api = ZoneAPI(zone)
                    incident_id_list = api.stop_mitigation()
                    msg += ' Auto stop mitigation was successful.'
                    tps2_logger.info(msg)
                    zone_es_logger.info(msg)
                except DeviceConfigurationError as exc:
                    msg += ' Failed to auto stop mitigation on zone: {}.'.format(exc.message)
                    tps2_logger.exception(msg)
                    zone_es_logger.error(msg)

                # Publish mitigation stopped event
                EventFactory.publish(
                    "a10.agalaxy.tps.ddos.zone.mitigation.stopped",
                    source_ip='127.0.0.1',
                    source_component="TPS",
                    description="DDOS zone mitigation stopped",
                    event_data={
                        'zone_id': str(zone.id),
                        'zone_name': zone.name,
                        'incident_id_list': [str(inc_id) for inc_id in incident_id_list]
                    }
                )
                # create web socket alert
                EventAlertFactory.publish(
                    AlertSourceType.INTERNAL,
                    source_name='localhost',
                    source_ip='127.0.0.1',
                    source_port='514',
                    source_component='TPS',
                    severity=AlertSeverity.ALERT,
                    description=msg)
        return response


class ZoneLearningView(APIView, ZoneActionMixin, TpsESLoggerMixin):
    """View for zone learning"""
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Get live indicator values"""
        zone = self.validate_zone()
        device_id = self.kwargs.get('device_id', None)
        # validate device ID
        if device_id:
            try:
                device = device_api.get_device_by_id(device_id)
            except:
                tps2_logger.exception('Failed to lookup device by ID %s', device_id)
                raise NotFound()
        zone_config = json.loads(zone.config)
        if zone_config['operational_mode'] == 'idle':
            return Response(status=400, data={'code': 400, 'message': 'Zone is idle.'})
        data = self.get_live_indicators(zone, device_id=device_id)
        return Response(status=200, data=data)

    def post(self, request, *args, **kwargs):
        """Start learning on zone and optionally schedule a learning duration"""
        # Parse POST body
        try:
            duration_in_mins = request.data.get('duration', None)
            sensitivity = request.data.get('sensitivity', 'default')
            algorithm = request.data.get('algorithm', 'max')
        except ParseError:
            duration_in_mins = None
            sensitivity = 'default'
            algorithm = 'max'

        # Validate
        zone = self.validate_zone()
        self.validate_algorithm(algorithm)
        self.validate_sensitivity(sensitivity)

        # Check if zone is in mitigation/error status
        if zone.status == DdosDstZone.STATUS_MITIGATION or zone.status == DdosDstZone.STATUS_ERROR:
            return Response(
                status=400,
                data={
                    'code': 400,
                    'message': 'Cannot start learning because zone is in mitigation/error status.'
                }
            )
        es_logger = self.get_es_logger(request)
        # Set the operational mode to learning
        zone_config = json.loads(zone.config)
        zone_config['operational_mode'] = 'learning'
        zone.config = json.dumps(zone_config)
        zone.save()
        # Push to devices
        try:
            new_api = ZoneAPI(id_or_instance=zone)
            new_api.push_support_objects()
            old_api = DdosDstZoneApi(instance=zone)
            old_api.configure_zone()
        except DeviceConfigurationError as exc:
            msg = 'Failed to configure learning mode for zone {} on device(s). Errors: {}.'.format(
                zone.name, exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)
            raise exc

        # Log success
        msg = 'Zone {} switched to learning mode.'.format(zone.name)
        tps2_logger.info(msg)
        es_logger.info(msg)

        if duration_in_mins is not None:
            try:
                duration_in_mins = int(duration_in_mins)
                if duration_in_mins <= 0:
                    msg = "Failed to set learning duration for zone {} due to invalid duration value.".format(zone.name)
                    msg += " Please stop learning manually."
                    tps2_logger.error(msg)
                    es_logger.error(msg)
                    return Response(status=400, data={'code': 400, 'message': msg})
            except Exception as exc:
                msg = "Failed to set learning duration for zone {} due to invalid duration value.".format(zone.name)
                msg += " Please stop learning manually. Error: {}.".format(exc.message)
                tps2_logger.exception(msg)
                es_logger.error(msg)
                return Response(status=400, data={'code': 400, 'message': msg})

        # Schedule learning duration if needed
        schedule_success = None
        if duration_in_mins:
            if 'TZ' in os.environ:  # get around the timezone problem
                del os.environ['TZ']
            start_datetime = datetime.datetime.now() + datetime.timedelta(minutes=duration_in_mins)
            start_datetime_str = start_datetime.strftime('%m/%d/%Y %I:%M %p')
            schedule_info = scheduler_utility.calculate_schedule(
                'schedule', start_datetime_str, "One Time", None, None, None)
            task_group_name = 'zone_learning_' + str(int(time.time()))
            description = "Scheduled learning duration ({} minutes) for zone {}. Sensitivity: {}".format(
                duration_in_mins, zone.name, sensitivity)
            task_executor = "executor_zone_learning_complete"
            username, domain = self.get_user_and_domain_from_request(request)
            payload_data = [{
                'zone_name': str(zone.name),
                'zone_id': str(zone.id),
                'sensitivity': sensitivity,
                'algorithm': algorithm,
                'user_name': username,
                'user_domain': domain
            }]
            schedule_success, body = scheduler_utility.schedule_task(
                username,
                task_group_name,
                task_executor,
                payload_data,
                description,
                **schedule_info)

            if schedule_success:
                # Add job to zone's meta data
                DdosDstZone.add_zone_learning_job(instance=zone, task_group_name=task_group_name)

        # Return appropriate response
        if duration_in_mins and not schedule_success:
            msg = 'Failed to schedule learning duration for zone {}.'.format(zone.name)
            msg += ' Please stop learning manually.'
            tps2_logger.error(msg)
            es_logger.error(msg)
            return Response(
                status=202,
                data={
                    'code': 202,
                    'message': 'Learning started but failed to schedule learning duration.'
                }
            )
        if duration_in_mins and schedule_success:
            msg = 'Zone learning duration scheduled for zone {}. Task: {}.'.format(zone.name, task_group_name)
            tps2_logger.info(msg)
            es_logger.info(msg)
            return Response(
                status=200,
                data={
                    'code': 200,
                    'message': 'Learning started successfully and learning duration has been scheduled.'
                }
            )
        # note: success message already logged earlier
        return Response(status=200, data={'code': 200, 'message': 'Learning started successfully.'})


class ZoneMonitorView(APIView, ZoneActionMixin, TpsESLoggerMixin):
    """View for zone monitoring"""
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Get the indicator values based on the algorithm and sensitivity multiplier"""
        zone = self.validate_zone()
        algorithm = request.query_params.get('algorithm', 'max')
        sensitivity = request.query_params.get('sensitivity', 'default')
        self.validate_algorithm(algorithm)
        self.validate_sensitivity(sensitivity)
        # Apply the algorithm and sensitivity
        multiplier = self.SENSITIVITY_MAP[sensitivity]
        data = self.calculate_indicator_values(zone, algorithm=algorithm, multiplier=multiplier)
        return Response(status=200, data=data)

    def post(self, request, *args, **kwargs):
        """Start monitoring. Values configured based on algorithm and sensitivity provided."""
        zone = self.validate_zone()
        sensitivity = request.data.get('sensitivity', 'default')
        algorithm = request.data.get('algorithm', 'max')
        manual_thresholds = request.data.get('manual_thresholds', False)
        zone_config = json.loads(zone.config)
        if not manual_thresholds:
            self.validate_algorithm(algorithm)
            self.validate_sensitivity(sensitivity)
            multiplier = self.SENSITIVITY_MAP[sensitivity]
            indicators = self.calculate_indicator_values(zone, algorithm=algorithm, multiplier=multiplier)
            # Get the number of devices
            zone_config = ZoneAPI.indicators_to_config(zone_config, indicators)

        es_logger = self.get_es_logger(request, uuid=str(zone.id))
        # Update the zone config
        zone_config['operational_mode'] = 'monitor'
        zone.config = json.dumps(zone_config)
        zone.save()

        try:
            # Unschedule jobs
            DdosDstZone.unschedule_all_zone_learning(zone)
        except Exception as exc:
            msg = 'Failed to unschedule zone learning jobs for zone {}. Error: {}.'.format(zone.name, exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)

        try:
            new_api = ZoneAPI(zone)
            new_api.push_support_objects()
            old_api = DdosDstZoneApi(instance=zone)
            old_api.configure_zone()
        except Exception as exc:
            msg = 'Zone {} switched to monitor mode'.format(zone.name)
            msg += ', but encountered error when configuring device(s). Error: {}.'.format(exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)
            raise exc

        msg = 'Zone {} switched to monitor mode.'.format(zone.name)
        tps2_logger.info(msg)
        es_logger.info(msg)
        return Response(status=200, data={'code': 200, 'message': 'Monitoring started successfully.'})


class ZoneIdleView(APIView, ZoneActionMixin, TpsESLoggerMixin):
    http_method_names = ['post', 'options']

    def post(self, request, *args, **kwargs):
        zone = self.validate_zone()
        if zone.status != DdosDstZone.STATUS_NORMAL:
            return Response(status=400, data={'code': 400, 'message': 'Please stop mitigation on zone firstly.'})

        es_logger = self.get_es_logger(request, uuid=str(zone.id))
        zone_config = json.loads(zone.config)
        zone_config['operational_mode'] = 'idle'
        zone.config = json.dumps(zone_config)
        zone.save()

        try:
            # Unschedule jobs
            DdosDstZone.unschedule_all_zone_learning(zone)
        except Exception as exc:
            msg = 'Failed to unschedule zone learning jobs for zone {}. Error: {}.'.format(zone.name, exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)

        try:
            # Push to devices
            new_api = ZoneAPI(zone)
            new_api.push_support_objects()
            old_api = DdosDstZoneApi(instance=zone)
            old_api.configure_zone()
        except Exception as exc:
            msg = 'Zone {} switched to idle mode'.format(zone.name)
            msg += ', but encountered error when configuring device(s). Error: {}.'.format(exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)
            raise exc

        msg = 'Zone {} switched to idle mode.'.format(zone.name)
        tps2_logger.info(msg)
        es_logger.info(msg)
        return Response(status=200, data={'code': 200, 'message': 'Zone mode set to idle.'})


class ZoneLogSettingsPushView(APIView, TpsESLoggerMixin):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        zone_id = self.kwargs.get('zone_id', None)
        if not zone_id:
            raise NotFound()
        try:
            zone = DdosDstZone.objects.get(id=zone_id)
        except ObjectDoesNotExist:
            raise NotFound()
        payload = json.loads(request.data)
        log_data = {
            'log_enable': payload.get('log_enable', False),
            'log_periodic': payload.get('log_periodic', False)
        }
        if log_data['log_periodic'] and not log_data['log_enable']:
            raise serializers.ValidationError({'log_periodic': 'Cannot be true if log_enable is false.'})

        es_logger = self.get_es_logger(request)

        try:
            zone_api = ZoneAPI(zone)
            zone_api.push_log_settings(log_data)
        except Exception as exc:
            msg = 'Failed to update log settings for zone {}. Error: {}.'.format(zone.name, exc.message)
            tps2_logger.exception(msg)
            es_logger.error(msg)
            raise exc

        msg = 'Zone {} log settings updated. Log enable: {}, Log periodic: {}.'.format(
            zone.name, log_data['log_enable'], log_data['log_periodic'])
        tps2_logger.info(msg)
        es_logger.info(msg)

        return Response(status=200, data={'code': 200, 'message': 'Zone log settings pushed to device(s).'})
