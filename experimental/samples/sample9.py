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
