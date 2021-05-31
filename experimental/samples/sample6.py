import os
import sys
import json
import time
import requests

from functools import partial
from upgrade_util import wait, check_for_deployments, handle_response, network_request, make_request

MARATHON_HOST = str(os.environ.get('MARATHON_HOST', failobj='marathon.mesos'))
MARATHON_PORT = str(os.environ.get('MARATHON_PORT', failobj='8080'))
MARATHON_ENDPOINT = "http://" + MARATHON_HOST + ':' + MARATHON_PORT
BUILD_NUMBER= os.environ.get('BUILD_NUMBER', failobj='0')

demo_upgrade_json="demo-upgrade.json"
latest_metadata_json="./versions/latest/apps/changed/metadata.json"
webhook_url="https://hooks.zapier.com/hooks/catch/523819/a46c4d/"
def get_metadata_version():
    # Check if we need to upgrade
    with open(latest_metadata_json, 'rb') as app_json_file:
        app_data=json.load(app_json_file)
        return app_data['container']['docker']['image']

def send_test_status(status):
    """Send test status to zapier via webhook"""
    status_obj = {}
    if status == "FAIL":
        status_obj = {"job": "update-demo", "result": "FAIL", "jenkins_build_url": "https://jenkins.netsil.io/job/upgrade-demo/" + BUILD_NUMBER + "/console"}
    elif status == "PASS":
        status_obj = {"job": "update-demo", "result": "PASS", "jenkins_build_url": "https://jenkins.netsil.io/job/upgrade-demo/" + BUILD_NUMBER + "/console"}
    requests.post(webhook_url,
                  json=status_obj,
                  headers={'Content-type': 'application/json', 'Accept': 'application/json'})

def install_upgrade_app():
    # Waiting for any deployments prior to the upgrade process to resolve
    wait(check_for_deployments, timeout=900)

    with open(demo_upgrade_json, 'rb') as app_json_file:
        success = make_request(requests.post,
                            MARATHON_ENDPOINT + '/v2/apps/',
                            json=json.load(app_json_file), headers={'Content-Type' : 'application/json'},
                            wait_type='deployments', wait_time=300,
                            msg="app creation", expected_code=201)
        if not success:
            print "Error: Unable to install upgrade app"
            send_test_status("FAIL")
            sys.exit(1)

def wait_for_completion(current_version):
    """Wait up to an hour for upgrade to finish
    """
    max_wait=3600
    period=60
    count=0

    while True:
        resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps/' + 'metadata'))
        new_version = resp.json()['app']['container']['docker']['image']
        if count > max_wait:
            print "Error: Upgrade taking too long, something may be wrong"
            send_test_status("FAIL")
            sys.exit(1)

        if current_version != new_version:
            print "Upgrade complete!"
            break
        else:
            print "Still upgrading..."

        time.sleep(period)
        count = count + period
        print "Waited " + str(count) + " seconds."

def main():
    # Get metadata version from demo
    resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps/' + 'metadata'))
    current_version = resp.json()['app']['container']['docker']['image']
    next_version = get_metadata_version()

    print "Current metadata demo version: " + str(current_version) + ", Next metadata demo version: " + str(next_version)
    if current_version == next_version:
        print "No need to upgrade as we are already at the latest version"
    else:
        install_upgrade_app()
        wait_for_completion(current_version)
    send_test_status("PASS")

main()
