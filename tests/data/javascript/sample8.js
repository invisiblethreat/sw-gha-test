import moment from 'moment';

export const API_VERSION = 2;
export const BASE_PAGE_TITLE = 'Company Telemetry';
export const BASE_PATH = '/cv';
export const ROOT_PATH = '/';
export const DEFAULT_APP_ID = 'devices';
export const IS_PRODUCTION = process.env.NODE_ENV === 'production';
export const IS_STAGING = process.env.GEIGER_ENV === 'staging';
export const FIRST_YEAR_RELEASED = 2017;
export const GEIGER_INFO = {
  hash: process.env.COMMIT_HASH_ENV,
  timestamp:
    process.env.COMMIT_TIMESTAMP_ENV ?
      parseInt(process.env.COMMIT_TIMESTAMP_ENV, 10) * 1000 : // Times in Geiger are in ms
      undefined,
  version: process.env.VERSION_NUM_ENV,
};
export const CARD_OBSERVABLE_ROOT_ID = 'card-root-id';

// This controls the display of things like API server selection and warning/error counts.
export const SHOW_DEV_FEATURES = !IS_PRODUCTION || IS_STAGING;

// When we deploy to CVP, we deploy a production build that's not on staging
export const IS_CVP_DEPLOYMENT = IS_PRODUCTION && !IS_STAGING;

export const CVP_DEV_CLUSTERS = {
  cvpDemo: {
    host: 'cvp-demo.sjc.companynetworks.com',
    username: 'a',
    password: 'a',
  },
  cvpnh: {
    // Pin CVP_NH_HOST to a specific host so we don't have to accept so many certs
    host: 'cvp11.nh.companynetworks.com',
    username: 'cvpadmin',
    password: 'arastra',
  },
};

export const MOCK_API_SERVER = 'mock';
export const MOCK_SCALE_API_SERVER = 'mockScale';
export const API_SERVERS_AAA = {
  NONE: 'none',
  CVP: 'cvp',
  OIDC: 'oidc',
};

function getLocalAAAType() {
  if (EnvConfig.ENABLE_OIDC_LOGIN) {
    return API_SERVERS_AAA.OIDC;
  }
  if (IS_STAGING) {
    return API_SERVERS_AAA.NONE;
  }
  return API_SERVERS_AAA.CVP;
}

export function getWebsocketUrl(host) {
  return `wss://${host}/api/v${API_VERSION}/wrpc/`;
}

export const API_SERVERS = {
  stagingNoAuth: {
    aaaType: API_SERVERS_AAA.NONE,
    label: 'Cloud Staging Cluster (no auth)',
    url: getWebsocketUrl('apiserver-noauth.staging.corp.company.io'),
  },
  staging: {
    aaaType: API_SERVERS_AAA.OIDC,
    label: 'Cloud Staging Cluster',
    url: getWebsocketUrl('www.staging.corp.company.io'),
  },
  eoscore: {
    aaaType: API_SERVERS_AAA.NONE,
    label: 'EosCore Staging Cluster',
    url: getWebsocketUrl('apiserver-eoscore.staging.corp.company.io'),
  },
  dev: {
    aaaType: API_SERVERS_AAA.NONE,
    label: 'Cloud Dev Cluster',
    url: getWebsocketUrl('www.dev.corp.company.io'),
  },
  cvpDemo: {
    aaaType: API_SERVERS_AAA.CVP,
    label: 'On-Prem Demo Cluster',
    url: getWebsocketUrl(CVP_DEV_CLUSTERS.cvpDemo.host),
  },
  cvpnh: {
    aaaType: API_SERVERS_AAA.CVP,
    label: 'On-Prem Nashua Cluster',
    url: getWebsocketUrl(CVP_DEV_CLUSTERS.cvpnh.host),
  },
  companyio: {
    aaaType: API_SERVERS_AAA.OIDC,
    label: 'Cloud Prod Cluster',
    url: getWebsocketUrl('www.company.io'),
  },
  mock: {
    aaaType: API_SERVERS_AAA.NONE,
    label: 'Mock Data',
    url: MOCK_API_SERVER,
  },
  mockScale: {
    aaaType: API_SERVERS_AAA.NONE,
    label: 'Mock Data (scale testing)',
    url: MOCK_SCALE_API_SERVER,
  },
  local: {
    aaaType: getLocalAAAType(),
    label: 'Local',
    url: getWebsocketUrl(window.location.host),
  },
};

export const API_SERVER_QUERY_PARAM = 'apiServer';

// Use the aeris rest path for now since it clearly returns either HTTP 200 or 401
// Change when CVPI implements publicly reachable auth check endpoint
export const CVP_CHECK_AUTH_PATH = '/api/v1/rest/';

export const CVP_AUTH_PATH = '/cvpservice/login/authenticate.do';
// Empty userId parameter is necessary; 404 returned without it
export const CVP_AUTH_USERINFO_PATH = '/cvpservice/login/getCVPUserProfile.do?userId=';
export const CVP_AUTH_LOGOUT_PATH = '/cvpservice/login/logout.do';
export const CVP_USER_COOKIE_PATH = '/web';
export const CVP_USER_COOKIE_MAX_AGE = moment.duration(1, 'day').asSeconds();
export const OAUTH_LOGOUT_PATH = '/api/v1/oauth?logout=true';

function getDefaultAPIServer() {
  if (process.env.DEFAULT_API_SERVER) {
    return process.env.DEFAULT_API_SERVER;
  }
  if (IS_PRODUCTION) {
    return IS_STAGING ? 'stagingNoAuth' : 'local';
  }
  return 'mock';
}

export const DEFAULT_API_SERVER = getDefaultAPIServer();



// WEBPACK FOOTER //
// ./src/constants/app.js