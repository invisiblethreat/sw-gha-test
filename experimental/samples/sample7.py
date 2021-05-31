import os
import subprocess
import logging
import sys
import requests
import json
import time

from json_delta import patch
import cluster_upgrade as clust
from bin.gen_deltas import gen_deltas, list_diff
from shutil import rmtree
from functools import partial
from upgrade_util import wait, check_for_deployments, handle_response, network_request, make_request

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

logging.info("Upgrading!")

LATEST_VERSION_NUMBER = str(os.environ.get('LATEST_VERSION_NUMBER', failobj='0.2.0'))
NEXT_TAG_LIST = str(os.environ.get('NEXT_TAG_LIST', failobj='master-0.2.1,master-0.2.2,master-0.2.3'))

CURRENT_VERSION_NUMBER = str(os.environ.get('CURRENT_VERSION_NUMBER', failobj='0.2.0'))

MARATHON_HOST = str(os.environ.get('MARATHON_HOST', failobj='marathon.mesos'))
MARATHON_PORT = str(os.environ.get('MARATHON_PORT', failobj='8080'))
MARATHON_ENDPOINT = "http://" + MARATHON_HOST + ':' + MARATHON_PORT

MESOS_HOST = str(os.environ.get('MESOS_HOST', failobj='leader.mesos'))
MESOS_PORT = str(os.environ.get('MESOS_PORT', failobj='5050'))
MESOS_ENDPOINT = "http://" + MESOS_HOST + ':' + MESOS_PORT

os.environ['NETSIL_VERSION_NUMBER'] = LATEST_VERSION_NUMBER
os.environ['BUILD_ENV'] = 'production'

class Upgrader():
    def __init__(self):
        self.set_apps_dir()
        self.upgrade_data = './versions/' + LATEST_VERSION_NUMBER + '/upgrade-data.tar.gz'
        self.app_endpoint_dir = './versions/' + LATEST_VERSION_NUMBER + '/' + self.apps_dir
        self.running_apps_dir = self.app_endpoint_dir + '/running'
        self.changed_apps_dir = self.app_endpoint_dir + '/changed'
        self.updated_apps_dir = self.app_endpoint_dir + '/updated'

        self.headers = {'Content-Type' : 'application/json'}

        # We should exclude these keys when fetching the app json
        self.status_info_keys = [
            'tasks',
            'taskKillGracePeriodSeconds',
            'tasksRunning',
            'tasksStaged',
            'tasksHealthy',
            'tasksUnhealthy',
            'taskStats',
            'deployments',
            'readiness',
            'lastTaskFailure',
            'version',
            'versionInfo',
            'fetch',
            'ports',
            'portDefinitions',
            'dependencies',
            'storeUrls',
            'gpus',
            'backoffFactor',
            'backoffSeconds',
            'upgradeStrategy',
            'maxLaunchDelaySeconds',
            'instances' # We don't want to scale down instances during upgrade
        ]

        # TODO: This should not be the final design. We shouldn't be hardcoding these variables in the upgrade repo.
        # Instead, we should generate a list of these user-config properties to a file from the AOC repo and import it into the upgrade repo.
        self.user_config_keys = [
            'env.DEEP_STORAGE',
            'env.S3_ENDPOINT',
            'env.druid_s3_accessKey',
            'env.druid_s3_secretKey',
            'env.druid_storage_baseKey',
            'env.druid_storage_bucket',
            'env.druid_storage_type',
            'env.RETENTION_PERIOD_DAYS',
            'env.RETENTION_PERIOD_MINUTES',
            'env.druid_indexer_logs_type',
            'env.druid_indexer_logs_s3Prefix',
            'env.druid_indexer_logs_s3Bucket',
            'env.USER_DB_HOST',
            'env.MYSQL_USER',
            'env.MYSQL_PASSWORD',
            'env.CLOUDSQL_INSTANCE'
        ]

        self.app_index = dict()

        # For scaling
        resp = network_request(partial(requests.get, MESOS_ENDPOINT + '/metrics/snapshot'))
        self.total_workers = int(resp.json()['master/slaves_active'])
        self.set_versions()

    def set_versions(self):
        # Generate version tag list
        # Set version list
        # Removal and addition for a specific version happens in lockstep
        # E.g. remove_i, add_i, remove_{i+1} add_{i+1}, ...
        # Reversing because we have put the latest version at the head (first in the list...)
        self.versions = [token.split('-')[-1] for token in NEXT_TAG_LIST.split(',')]
        self.versions.reverse()

        # For non-stable/staging branches
        if LATEST_VERSION_NUMBER == "latest":
            self.versions = ['latest']

        logging.info("VERSIONS " + str(self.versions))

    def is_stable_staging(self):
        resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps/' + 'metadata'))
        app_env = resp.json()['app']['env']
        return 'NETSIL_BUILD_BRANCH' in app_env and (app_env['NETSIL_BUILD_BRANCH'] == 'staging' or app_env['NETSIL_BUILD_BRANCH'] == 'stable')

    def is_ha(self):
        resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps/' + 'metadata'))
        app_env = resp.json()['app']['env']
        return 'IS_HA' in app_env and app_env['IS_HA'] == 'yes'

    def set_apps_dir(self):
        if self.is_ha():
            self.apps_dir = 'ha-apps'
        else:
            self.apps_dir = 'apps'

    def reorder_apps(self, app_reorders, app_list):
        # First, remove all the apps that we wish to reorder from the app list
        apps_to_upgrade = list()
        for app_token in sorted(app_reorders):
            app = app_token[1]
            if app in app_list:
                app_list.remove(app)
                apps_to_upgrade.append(app)

        # Then, reinsert them to the end of the list in order
        app_list.extend(apps_to_upgrade)
        return app_list

    def update_app_index(self):
        resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps'))
        apps = resp.json()['apps']
        for app in apps:
            # We trim the leading "/"
            app_id = app['id'][1:]
            self.app_index[app_id] = app

    def run_script_by_version(self, script):
        if self.is_ha() and self.is_stable_staging():
            logging.info("Warning! Skipping pre app upgrade for previous versions because we're in stable or staging")
            return

        for version in self.versions:
            logging.info("Running pre-app-upgrade.sh for version " + str(version))
            self.run(script, version=version)
            logging.info("Finished pre-app-upgrade.sh for version " + str(version))

    def remove_apps_by_version(self):
        if self.is_ha() and self.is_stable_staging():
            logging.info("Warning! Skipping app removal because we're in stable or staging")
            return

        for version in self.versions:
            # Removal
            removed_file = './versions/' + str(version) + '/' + self.apps_dir + '/REMOVED'
            if os.path.isfile(removed_file):
                with open(removed_file) as f:
                    removed_apps = [line.strip() for line in f]
                if not self.remove_apps(removed_apps):
                    logging.info("App removal failed!")
                    exit(-1)
            else:
                logging.info("Warning: REMOVED file for version " + str(version) + " not found.")

    def add_apps(self):
        # Add apps based on their non-existence in the currently running cluster
        # This is convenient if we have to remove and add the same app in an upgrade, due to changes in persistent volumes
        added_app_files = self.resolve_changed_apps()
        added_app_jsons = list()
        for app in os.listdir(self.changed_apps_dir):
            if app in added_app_files and app.endswith(".json"):
                with open(self.changed_apps_dir + '/' + app, 'rb') as app_json_file:
                    logging.info("Adding app: " + str(app))
                    added_app_jsons.append(app_json_file.read())

        if not self.create_apps(added_app_jsons):
            logging.info("App creation failed!")
            exit(-1)

    def update_apps(self):
        if os.path.isdir(self.updated_apps_dir):
            app_deltas = list()
            for app in os.listdir(self.updated_apps_dir):
                if app.endswith(".json"):
                    app_deltas.append(app)

            app_reorders = [(-3, 'alerts.patch.json'), (-2, 'druid-coordinator.patch.json'), (-1, 'metadata.patch.json')]
            app_deltas = self.reorder_apps(app_reorders, app_deltas)

            self.reconfigure_apps(app_deltas)
        else:
            logging.info("Error: " + self.updated_apps_dir + " does not exist." )
            exit(-1)

    def upgrade_apps(self):
        if os.path.isdir(self.app_endpoint_dir):
            # Waiting for any deployments prior to the upgrade process to resolve
            wait(check_for_deployments, timeout=600)

            # Remove apps by order of version
            self.remove_apps_by_version()

            # Update app index after we've done removals
            self.update_app_index()

            # Add apps
            self.add_apps()

            # Update app index after we've done additions
            self.update_app_index()

            # Reconfigure (e.g. update) apps.
            self.update_apps()
        else:
            logging.info("Warning: " + self.app_endpoint_dir + " does not exist." )
            exit(-1)

    def upgrade_cluster(self, cluster_upgrade_cmd):
        """Performs cluster upgrades."""
        logging.info("upgrade data: " + str(self.upgrade_data))
        wait(clust.check_for_cluster_upgrades, timeout=1800, marathon_endpoint=MARATHON_ENDPOINT)
        wait(check_for_deployments, timeout=1800)
        if os.path.isfile(self.upgrade_data):
            logging.info("Found upgrade data")
            os.environ['CLUSTER_UPGRADE_CMD'] = cluster_upgrade_cmd

            workers = clust.get_mesos_workers(mesos_endpoint=MESOS_ENDPOINT)
            logging.info("Running cluster upgrade on workers: " + str(workers))

            clust.template_cluster_upgrade(workers, os.environ, '/tmp/cluster-upgrade-staging', cluster_upgrade_cmd.split('.')[0])

            resp = clust.install_upgrade_apps('/tmp/cluster-upgrade-staging', marathon_endpoint=MARATHON_ENDPOINT)
            handle_response(resp, msg="cluster upgrade app creation", expected_code=201)

            # Wait 2 seconds for cluster upgrade app id to be populated in marathon
            time.sleep(2)

            # Wait up to 30 min. Cluster upgrades entail downloading images, so it can take a while
            wait(clust.check_for_cluster_upgrades, timeout=1800, marathon_endpoint=MARATHON_ENDPOINT)
        else:
            logging.info("Upgrade cluster script " + cluster_upgrade_cmd + " not found, so not running it")

    def run(self, script, version=LATEST_VERSION_NUMBER):
        # For non-stable/staging branches
        script_path = './versions/' + version + '/' + script
        script_stdout = open('/var/log/netsil/' + script + '_' + version + '.log', 'ab')
        script_stderr = open('/var/log/netsil/' + script + '_' + version + '.err', 'ab')
        script_env = os.environ.copy()
        script_env['CURRENT_VERSION_NUMBER'] = version

        if os.path.isfile(script_path):
            logging.info("Running script.")
            results = subprocess.Popen(["/bin/sh", script_path],
                            env=script_env,
                            stdout=script_stdout,
                            stderr=script_stderr,
                            shell=False,
                            preexec_fn=os.setpgrp)
            _, _ = results.communicate()
            ret_code = results.returncode
            if ret_code != 0:
                logging.info("Error! Running " + str(script) + " failed!")
                exit(ret_code)
        else:
            logging.info("Script " + script_path + "not found, so not running it.")
        script_stdout.close()
        script_stderr.close()

    def filter_user_config_keys(self, app_json):
        """This takes in an object and filters (e.g. removes) the object by the list of keys in self.user_config_keys.
        Currently, it only works for marathon config in the form of the <env> object."""
        for key in self.user_config_keys:
            parent_key, user_key = key.split('.')
            if parent_key not in app_json.keys():
                logging.info("Warning! Parent key for user config filter not found in app_json")
            else:
                parent_obj = app_json[parent_key]
                if user_key in parent_obj.keys():
                    user_val = parent_obj.pop(user_key)
                    logging.info("Removing <key, val> " + str(user_key)  + ',' + str(user_val) + " from delta-sequence directives.")

        return app_json

    def resolve_changed_apps(self):
        """This generates delta-sequences from the current marathon app state
        and the apps in ./versions/${version}/apps/added"""

        # We must wait for any deployments to finish before generating delta-sequences
        wait(check_for_deployments, timeout=600)

        running_apps_dir = self.running_apps_dir

        rmtree(running_apps_dir, ignore_errors=True)
        os.makedirs(running_apps_dir)

        rmtree(self.updated_apps_dir, ignore_errors=True)
        os.makedirs(self.updated_apps_dir)

        # Remove the user config keys from running directory
        for app_id in self.app_index.keys():
            resp = network_request(partial(requests.get, MARATHON_ENDPOINT + '/v2/apps/' + app_id))
            with open(running_apps_dir + '/' + app_id + '.json', 'w') as app_json_file:
                app_json = resp.json()['app']
                status_filtered_json = { k : v for k, v in app_json.iteritems() if v and k not in self.status_info_keys}
                filtered_json = self.filter_user_config_keys(status_filtered_json)
                json.dump(filtered_json, app_json_file)

        # Removes the user config keys from changed directory as well
        # NOTE: More or less the same code as above...refactor later
        # Need this for when env vars are changed at initial setup, but should not be changed to the defaults on further upgrades
        # e.g. USER_DB_HOST, MYSQL_USER, MYSQL_PASSWORD
        changed_apps = dict()
        for app_id in self.app_index.keys():
            app_json_filepath = self.changed_apps_dir + '/' + app_id + '.json'
            if os.path.isfile(app_json_filepath):
                with open(app_json_filepath, 'r') as app_json_file:
                    app_json = json.load(app_json_file)
                    status_filtered_json = { k : v for k, v in app_json.iteritems() if v and k not in self.status_info_keys}
                    filtered_json = self.filter_user_config_keys(status_filtered_json)
                    changed_apps[app_id] = filtered_json

        for app_id in self.app_index.keys():
            app_json_filepath = self.changed_apps_dir + '/' + app_id + '.json'
            if os.path.isfile(app_json_filepath):
                with open(app_json_filepath, 'w') as app_json_file:
                    json.dump(changed_apps[app_id], app_json_file)

        # Get list of apps to ignore
        ignore_apps = []
        ignore_file = './versions/' + LATEST_VERSION_NUMBER + '/apps/IGNORE'
        if os.path.isfile(ignore_file):
            with open(ignore_file) as f:
                ignore_apps = [app_id + '.json' for app_id in [line.strip() for line in f] if app_id is not '']
        else:
            logging.warning("Warning: IGNORE file for version " + str(version) + " not found.")

        # Generate delta sequences
        added_apps = gen_deltas(running_apps_dir,
                   self.changed_apps_dir,
                   self.updated_apps_dir)

        return list_diff(added_apps, ignore_apps)

    def remove_apps(self, removed_apps):
        for app_id in removed_apps:
            success = make_request(requests.delete, MARATHON_ENDPOINT + '/v2/apps/' + app_id)
            logging.info("Removing app " + str(app_id))
            if not success:
                return False
        return True

    def create_apps(self, added_app_jsons):
        for app_json in added_app_jsons:
            success = make_request(requests.post,
                                MARATHON_ENDPOINT + '/v2/apps/',
                                json=json.loads(app_json), headers=self.headers,
                                wait_type='deployments', wait_time=300,
                                msg="app creation", expected_code=201)
            if not success:
                return False
        return True

    def gen_patch(self, current_app_id, delta_sequence):
        """Applies patch to current config through the json-delta format.
        """
        # Get the current (old) state of the json we're updating
        current_app_state = self.app_index[current_app_id]

        # Apply the patch
        final_app_state = patch(current_app_state, delta_sequence, in_place=False)
        toplevel_keys = { node[0][0] for node in delta_sequence }
        return toplevel_keys, final_app_state

    def apply_config(self, current_app_id, toplevel_keys, final_app_state):
        """Applies patched config to marathon
        This is why we need json-deltas -- to tell us which keys have changed.
        """

        logging.info("Updating app: " + current_app_id + " with keys: " + str(toplevel_keys))
        updated_app_state =  { key: final_app_state[key] for key in toplevel_keys if key in final_app_state }
        make_request(requests.put,
                    MARATHON_ENDPOINT + '/v2/apps/' + current_app_id,
                    json=updated_app_state, headers=self.headers,
                    wait_type='deployments', wait_time=300,
                    msg="app reconfigure for " + str(current_app_id), expected_code=200)

    def reconfigure_apps(self, app_deltas):
        """Reconfigures a marathon app with PUT
        """
        logging.info("Reconfiguring apps: " + str(app_deltas))
        for app in app_deltas:
            with open(self.updated_apps_dir + '/' + app) as app_delta:
                # Typically, we name the JSON files in the "changed" folder <app-id>.patch.json
                app_id = app.split('.')[0]

                # We need to scale to 0 because of the unique hostname constraint
                #make_request(requests.put,
                #             MARATHON_ENDPOINT + '/v2/apps/' + app_id,
                #             json={'instances': 0}, headers=self.headers,
                #             wait_type='deployments', wait_time=300,
                #             msg="app suspend for " + str(app_id), expected_code=200)

                toplevel_keys, final_app_state = self.gen_patch(app_id, json.load(app_delta))
                self.apply_config(app_id, toplevel_keys, final_app_state)

                # Retrieve app state again after it's done reconfiguring.
                self.update_app_index()

        # Scale
        app_reorders = [(-3, 'alerts'), (-2, 'druid-coordinator'), (-1, 'metadata')]
        app_id_list = self.reorder_apps(app_reorders, self.app_index.keys())
        for app_id in app_id_list:
            app_instances = self.get_scale(app_id)
            make_request(requests.put,
                        MARATHON_ENDPOINT + '/v2/apps/' + app_id,
                        json={'instances': app_instances}, headers=self.headers,
                        wait_type='deployments', wait_time=300,
                        msg="app rescale for " + str(app_id), expected_code=200)

    def get_scale(self, app_id):
        app_dict = self.app_index[app_id]
        if app_dict['env'].get('DO_SCALE', "").lower() == "yes":
            logging.info("Scaling app " + str(app_id) + " to " + str(self.total_workers) + " instances.")

            return self.total_workers
        else:
            logging.info("App " + str(app_id) + " is not set to scale.")
            return 1

upgrader = Upgrader()

# TODO: Check that all the exit(-1) calls can't happen by accident
upgrader.upgrade_cluster('download.sh')
upgrader.upgrade_cluster('platform.sh')

# Before any apps are upgraded, or any migrations are done
upgrader.run_script_by_version("pre-app-upgrade.sh")

# Also does app removal and addition
upgrader.upgrade_apps()

# After the apps are upgraded
upgrader.run("post-app-upgrade.sh")

# AOC is operational at this point
upgrader.upgrade_cluster('cleanup.sh')

logging.info("Finished upgrade!")
