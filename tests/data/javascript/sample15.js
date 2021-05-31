import os from 'os';
import includes from 'lodash/includes';
import {transform} from 'hoek';

const Config = function (defaults) {
    for (var key in defaults) {
        if (defaults.hasOwnProperty(key)) {
            Object.defineProperty(this, key, Object.getOwnPropertyDescriptor(defaults, key));
        }
    }
}

/**
 * Override config values that are already set in this config
 * @param {Object} conf the map of overriding key-values
 */
Config.prototype.set = function (conf) {
    for (var key in this) {
        if (this.hasOwnProperty(key) && conf.hasOwnProperty(key)) {
            this[key] = conf[key];
        }
    }

    return this;
};

/**
 * Prune only a select set of config values (to ship to the client for ex.)
 * @return {Object} the object representing this pruned config
 */
Config.prototype.dehydrate = function () {
    const dehydrated = [
        'standalone',
        'features',
        'PRODUCT_FRONTEND_VERSION',
        'PRODUCT_VERSION_NUMBER',
        'PRODUCT_BUILD_BRANCH',
        'PRODUCT_BUILD_NUMBER',
        'PRODUCT_COMMIT_HASH',
        'PIXELS_PER_DATAPOINT',
        'WEBSERVER_MOUNT_PATH',
        'DOCS_URL',
        'DCOS_PORT',
        'segmentDotIoKey',
        'isHA'
    ].reduce((acc, c) => {
        acc[c] = this[c];

        return acc;
    }, {});

    // deep property mapping {target: source}
    Object.assign(dehydrated, transform(this, {
        'sentry.dsn': 'sentry.dsnPublic',
        'sentry.enabled': 'sentry.enabled'
    }));

    return new Config(dehydrated);
};

const isPro = (process.env.PRODUCT_FLAVOR === 'Pro');
const isProductionBranch = includes(['stable', 'staging'], process.env.PRODUCT_BUILD_BRANCH);

const config = new Config({
    development: false,
    standalone: !isPro,
    isCloud: false,
    isHA: process.env.IS_HA === 'yes',
    cloudProvider: null, // 'aws'
    EC2_METADATA_HOST: 'http://169.254.169.254/latest/meta-data/instance-id',
    REDIS_HOST: '127.0.0.1',
    REDIS_PORT: 6379,
    sessionTTL: 10 * 24 * 3600 * 1000, // 10 days
    default_api_timeout: 15000,
    PRODUCT_BUILD_BRANCH: '',
    PRODUCT_FRONTEND_VERSION: '0.2.0',
    PIXELS_PER_DATAPOINT: 2.5,
    PRODUCT_VERSION_NUMBER: '',
    PRODUCT_COMMIT_HASH: '',
    PRODUCT_BUILD_NUMBER: '',
    PRODUCT_FLAVOR: '',
    WEBSERVER_MOUNT_PATH: '',
    CERT_FILE_PATH: '',
    KEY_FILE_PATH: '',
    STUNNEL_PID_FILE: '',
    MARATHON_HOST: process.env.MARATHON_HOST || 'marathon.mesos:8080',
    MESOS_HOST: 'leader.mesos:5050',
    MESOS_LEADER: 'leader.mesos',
    DCOS_PORT: '4443',
    segmentDotIoKey: '2EHEcAl9IKV5qkUSJAoNDftByqGXrF9x',
    sentry: {
        publicKey: '60e186bb278f4f88b9d8437880b742ff',
        secretKey: '48fd432e2b564209a7e672041e4aa920',
        projectId: '133810',
        get dsnPrivate() {
            return `https://${this.publicKey}:${this.secretKey}@sentry.io/${this.projectId}`;
        },
        get dsnPublic() {
            return `https://${this.publicKey}@sentry.io/${this.projectId}`;
        },
        get enabled() {
            return (!config.development || process.env.ENABLE_SENTRY === 'true');
        }
    },
    get DOCS_URL() {
        const baseURL = 'https://docs.product.company.com';
        var version = process.env.PRODUCT_DOCS_VERSION ||
                      process.env.PRODUCT_VERSION_NUMBER;

        version = (this.development || !version) ? 'latest' : `v${version}`;

        return `${baseURL}/${version}`;
    },
    get httpPort() {

        return this.development ? 80 : process.env.HTTP_LOCAL_PORT || 80;
    },
    get wsPort() {

        return this.development ? 8081 : process.env.WS_LOCAL_PORT || 81;
    },
    get productVersion() {
        return process.env.PRODUCT_VERSION_NUMBER || '0.2.0';
    },
    httpsProxyPort: process.env.HTTPS_REMOTE_PORT || 443,
    api_server: {
        host: process.env.API_SERVER_HOST || '127.0.0.1',
        port: process.env.API_SERVER_PORT || 8888
    },
    alerts_service: {
        host: process.env.ALERTS_SERVICE_HOST || '127.0.0.1',
        port: process.env.ALERTS_SERVICE_PORT || 8881
    },
    user_persistence_server: {
        host: process.env.USER_PERSISTENCE_HOST || '127.0.0.1',
        port: process.env.USER_PERSISTENCE_PORT || 8891
    },
    superuser_service: {
        host: process.env.SUPERUSER_HOST || '127.0.0.1',
        port: process.env.SUPERUSER_PORT || 8443
    },
    topology_service: {
        host: process.env.TOPOLOGY_SERVICE_HOST || '127.0.0.1',
        port: process.env.TOPOLOGY_SERVICE_PORT || 9002
    },
    query_service: {
        host: process.env.TIME_SERIES_ENDPOINT_HOST || '127.0.0.1',
        port: process.env.TIME_SERIES_ENDPOINT_PORT || 9047
    },
    metadata_service: {
        host: process.env.METADATA_HOST || '127.0.0.1',
        port: process.env.METADATA_PORT || 5444
    },
    license_manager_service: {
        host: process.env.LICENSE_MANAGER_SERVICE_HOST || '127.0.0.1',
        port: process.env.LICENSE_MANAGER_SERVICE_PORT || 9009
    },
    backups_service: {
        host: process.env.BACKUPS_HOST || '127.0.0.1',
        port: process.env.BACKUPS_PORT || 9093
    },
    sp_load_balancer: {
        host: process.env.PRODUCT_SP_LOAD_BALANCER_HOST || '127.0.0.1',
        port: process.env.PRODUCT_SP_LOAD_BALANCER_PORT || 5005
    },
    notifications_service: {
        host: process.env.NOTIFICATIONS_SERVICE_HOST || '127.0.0.1',
        port: process.env.NOTIFICATIONS_SERVICE_PORT || 9988
    },
    package_repo: {
        protocol: process.env.PRODUCT_PKG_REPO_PROTOCOL || 'https',
        host: process.env.PRODUCT_PKG_REPO_HOST || 'repo.product.company.com',
        port: process.env.PRODUCT_PKG_REPO_PORT || 443
    },
    own_server: {
        get hosts() {
            var interfaces = os.networkInterfaces();
            var addresses = [];
            for (var k in interfaces) {
                for (var k2 in interfaces[k]) {
                    var address = interfaces[k][k2];
                    if (address.family == 'IPv4' && !address.internal) {
                        addresses.push(address.address)
                    }
                }
            }
            return addresses;
        },
        get port() {
            return config.httpPort;
        },
        get productversion() {
            return config.productVersion;
        }
    },
    // PLEASE USE A DESCRIPTIVE, SUPER LONG NAME FOR THESE FEATURES
    features: {
        topologyGraphSettings: false,
        searchBar: true,
        serviceTooltipMoreBtn: false,
        userProfileServiceBtn: false,
        userProfileDashboardsTab: false,
        //The feature flags below have been added to hide serviceProfile timeline, dependencies, and people.
        //Haven't been able to test it still
        serviceProfileEndpoint: false,
        userWatchedServices: false,
        displayServiceErrorRate: false,
        extraSMTPFields: false,
        clusterManagement: isPro,
        manualAOCUpgrade: !isPro,
        tract: !isProductionBranch,
        eventSource: !isProductionBranch,
        authKeysConfig: true
    }
});

module.exports = config;
