/* eslint-disable no-console,max-lines,no-multi-str,no-process-exit,global-require,no-param-reassign,no-useless-escape */
/* eslint-disable import/order */
/*globals console */

const url = require('url');
const fs = require('fs');
const path = require('path');
const httpProxy = require('http-proxy');
const express = require('express');
const nopt = require('nopt');
const session = require('express-session');
const RedisStore = require('connect-redis')(session);
const helmet = require('helmet');
const compression = require('compression');
const sentry = require('raven');
const http = require('http');
const config = require('./config');
const {logger, loggerMiddleware} = require('./middleware/logger');

const parsedArgs = nopt({
    'help': Boolean,
    'api_server': String,
    'user_persistence_server': String,
    'topology_service': String,
    'development': Boolean
});

config.set(process.env).set(parsedArgs);

if ('help' in parsedArgs) {
    console.log('\nUsage: node/nodejs server.js\n\
Optional arguments:\n\
\t--api_server=<api server address:port>\n\
\t--user_persistence_server=<authentication server address:port>\n\
\t--topology_service=<topology service address:port>\n\
\t--query_service=<query service address:port>');
    process.exit();
}

function parseHost(hostUrl) {
    const parsedHost = url.parse(hostUrl);

    return {
        host: parsedHost.hostname,
        port: parsedHost.port
    };
}

// TODO: pretty sure host and post are always concatenated later
// so we could get rid of this
if (parsedArgs.hasOwnProperty('api_server')) {
    config.api_server = parseHost(parsedArgs.api_server);
}
if (parsedArgs.hasOwnProperty('user_persistence_server')) {
    config.user_persistence_server = parseHost(parsedArgs.user_persistence_server);
}
if (parsedArgs.hasOwnProperty('topology_service')) {
    config.topology_service = parseHost(parsedArgs.topology_service);
}
if (parsedArgs.hasOwnProperty('query_service')) {
    config.query_service = parseHost(parsedArgs.query_service);
}

const {
    dsnPrivate: sentryDSN,
    enabled: isSentryEnabledForEnv
} = config.sentry;

let isSentryInstanceEnabled = true;

const {
    EPOCH_FRONTEND_VERSION,
    EPOCH_BUILD_BRANCH,
    EPOCH_BUILD_NUMBER,
    EPOCH_COMMIT_HASH
} = config;

const STATIC_ASSETS_CACHE_EXPIRE = config.development ? 0 : 3600 * 1000; // 1 hour
const STATIC_ASSETS_PATH = `/v/${EPOCH_FRONTEND_VERSION}`;

const sentryOptions = {
    release: `${EPOCH_BUILD_BRANCH}-${EPOCH_FRONTEND_VERSION}-${EPOCH_COMMIT_HASH}.${EPOCH_BUILD_NUMBER}`,
    tags: {
        runtime: 'server',
        EPOCH_FRONTEND_VERSION,
        EPOCH_BUILD_BRANCH,
        EPOCH_BUILD_NUMBER,
        EPOCH_COMMIT_HASH
    },
    shouldSendCallback: () => isSentryInstanceEnabled && isSentryEnabledForEnv
};

const enableSentry = (enabled) => isSentryInstanceEnabled = enabled;


const sessionStore = new RedisStore({
    host: config.REDIS_HOST,
    port: config.REDIS_PORT
});

sessionStore.on('disconnect', function () {
    logger.log('error', 'Session store disconnected.');
});

const app = express();

if (isSentryEnabledForEnv) {
    sentry.config(sentryDSN, sentryOptions).install();
    app.use(sentry.requestHandler());
}
app.use(helmet());
app.use(compression());

// all environments
app.set('view engine', 'jade');
app.use(express.favicon(path.join(__dirname, '../public/img/favicon.ico')));
app.use(express.logger('dev'));
app.use(express.json({strict: false}));
app.use(express.urlencoded());
app.use(express.methodOverride());
app.use(express.cookieParser('your secret here'));

app.set('trust proxy', !config.development && !config.runInCI);
app.use(session({
    name: 'epoch.frontend',
    resave: !config.development,
    saveUninitialized: false,
    rolling: !config.development,
    store: sessionStore,
    secret: 'q0fpgi3dkcm79Dk',
    cookie: {
        secure: !config.development && !config.runInCI,
        maxAge: config.sessionTTL
    }
}));

app.use(function(req, res, next) {
    if (!config.development && !config.runInCI) {
        req.headers['x-forwarded-proto'] = 'https';
    }

    return next();
});

app.use(loggerMiddleware({logger}));

app.use(config.WEBSERVER_MOUNT_PATH, app.router);
app.use(config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH, express.static(path.join(__dirname, '../public'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH, express.static(path.join(__dirname, '../build'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(`${config.WEBSERVER_MOUNT_PATH}/assets`, express.static(path.join(__dirname, '../build/js/assets'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(`${config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH}/react-grid-layout/css`, express.static(path.join(__dirname, '../node_modules/react-grid-layout/css'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(`${config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH}/react-grid-layout/resizable/css`, express.static(path.join(__dirname, '../node_modules/react-grid-layout/node_modules/react-resizable/css'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(`${config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH}/codemirror`, express.static(path.join(__dirname, '../node_modules/codemirror/lib'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
app.use(`${config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH}/react-toggle`, express.static(path.join(__dirname, '../node_modules/react-toggle'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));
//TODO remove below line when webpack-dev-server will be used.
app.use(`${config.WEBSERVER_MOUNT_PATH + STATIC_ASSETS_PATH}/socket-io-client`, express.static(path.join(__dirname, '../node_modules/socket.io-client/dist'), {maxAge: STATIC_ASSETS_CACHE_EXPIRE}));

if (isSentryEnabledForEnv) {
    app.use(sentry.errorHandler());
}

app.use(require('./middleware/error-404.js'));
app.use(require('./middleware/error.js'));

app.set('views', path.join(__dirname, '../public'));
app.engine('html', require('ejs').renderFile);

logger.log('info', `Proxy host and port: ${config.api_server.host} ${config.api_server.port}`);
logger.log('info', `Topology service host and port: ${config.topology_service.host} ${config.topology_service.port}`);

const {authenticate, ensureSuperuser} = require('./middleware/ensure-authenticated');
const setHeaders = require('./middleware/set-headers');
const indexMiddleware = require('./middleware/index')({config, enableFeedback: enableSentry});
const login = require('./middleware/login')(config);
const licenseManager = require('./middleware/license-manager')(config);
const upgrading = require('./middleware/upgrading')(config);
const sentryManagementMiddleware = require('./middleware/sentry-management')(config, enableSentry);
const userPersistenceMiddleware = require('./middleware/user-persistence')(config);
const authApiMiddleware = require('./middleware/auth-api');
const forward = require('./middleware/forward');
const userPersistenceApiForwarder = require('./controllers/user-persistence-forwarder');

app.all(/^\/query\/internal(\/.*)?/, require('./middleware/error-404.js'));

app.all(/^\/api\/v(\d+)\/([^\/]*)(\/.*)?/, authenticate, setHeaders, require('./middleware/api'));

app.all(new RegExp(config.user_persistence_server.prefix), userPersistenceApiForwarder);

// status check
app.get('/ping', (req, res) => {
    res.send('pong');
});

app.get(/\/amazon\/.*/, forward(`http://${config.task_scheduler_service.host}:${config.task_scheduler_service.port}`));

app.get('/auth-api/verify', authApiMiddleware);
app.get('/(index)?', authenticate, indexMiddleware);
app.get('/config', require('./controllers/config')(config));
app.get('/login', login.get);
app.get('/saml/sp/metadata.xml', login.samlMetadata);
app.get('/logout', require('./middleware/logout'));
app.get('/reset/:token', require('./middleware/password-reset').get);
app.get('/retrieve-user-config-info', authenticate, require('./middleware/user-config.js'));
app.get('/terms', require('./middleware/terms'));
app.get('/getRpcapdConfigFile', require('./middleware/rpcapd'));
app.get('/install_epoch_collectors', require('./middleware/install-epoch-collectors').forward);
app.get('/get_collectors_dcos', require('./middleware/get-collectors-dcos'));
app.get('/epoch-collectors(:versionInfo)', require('./middleware/epoch-collectors').forward);
app.get('/setup_rpcap', require('./middleware/rpcapd-setup'));
app.get('/docs-info', authenticate, require('./middleware/docs-info'));
app.get(/^\/api\/.*/, authenticate, ensureSuperuser, setHeaders, require('./middleware/service').get);
app.get('/dashboard/clone/:dashboardId', authenticate, setHeaders, require('./middleware/dashboard').clone); // TODO delete still used in angular
app.get('/dashboard/templates', authenticate, setHeaders, require('./middleware/dashboard').forward);
app.get('/dashboard/view/:dashboardId', authenticate, setHeaders, require('./middleware/dashboard').forward);
app.get('/version', require('./middleware/version'));
app.get('/metadata-version', require('./middleware/metadata-version'));
app.get('/upgrading', upgrading.get);
app.get('/license/key', authenticate, licenseManager.key);
app.get('/webhook/:name', authenticate, require('./middleware/webhook').get);
app.get('/subscription', authenticate, require('./middleware/subscription-manager'));
app.get('/sp-load-balancer/info', authenticate, require('./middleware/url-deprefixer')('/sp-load-balancer'), require('./middleware/sp-load-balancer'));

app.post('/registration', userPersistenceMiddleware.firstTimeConfig);
app.post('/login', login.post);
app.post('/signup-users', authenticate, require('./middleware/signup-users'));
app.post('/verify-instance', require('./middleware/verify-instance'));
app.post('/forgot', require('./middleware/password-forgot'));
app.post('/reset/:token', require('./middleware/password-reset').post);
app.post('/signup', require('./middleware/signup'));
app.post(/^\/api\/.*/, authenticate, ensureSuperuser, setHeaders, require('./middleware/service').post);
app.post('/dashboard/clone/:dashboardId', authenticate, setHeaders, require('./middleware/dashboard').clone);
app.post('/search', require('./middleware/aoc-search'));
app.post('/license/activate', licenseManager.activate);
app.post('/license/register', licenseManager.register);
app.post('/license/update', licenseManager.update);
app.post('/license/verify', licenseManager.verify);
app.post('/error-reporting', authenticate, sentryManagementMiddleware);
app.post('/user-persistence/configure', userPersistenceMiddleware.configure);
app.post('/user-persistence/test', userPersistenceMiddleware.testConnection);

app.delete(/^\/api\/.*/, authenticate, require('./middleware/service').del);

app.all(/^\/query\/.*/, authenticate, setHeaders, require('./middleware/query'));
app.all('/auth-api/login', authApiMiddleware);
app.all(/^\/auth-api\/.*/, authenticate, setHeaders, authApiMiddleware);
app.all(/^\/alert\/*/, authenticate, setHeaders, require('./middleware/alerts'));
app.all(/^\/(user|service)(\/.*)?/, authenticate, authApiMiddleware);
app.all('/dashboards/:dashboardId?', authenticate, setHeaders, require('./middleware/dashboard').crud);
app.all('/druid-deep-store', authenticate, ensureSuperuser, forward(`http://${config.superuser_service.host}:${config.superuser_service.port}`));
app.all('/backups/:endpoint', authenticate, ensureSuperuser, forward(`http://${config.superuser_service.host}:${config.superuser_service.port}`));

try {
    fs.mkdirSync(path.join(__dirname, '../public/cache-forms'));
} catch (err) {
    if (err.code !== 'EEXIST') {
        throw err;
    }
}

const server = http.createServer(app);
const proxy = new httpProxy.createProxyServer();

server.on('upgrade', function (req, socket, head) {
    let connType = '';

    if (req.url.indexOf('/query/') === 0) {
        connType = 'query';
    } else if (req.url.indexOf('/live/') === 0) {
        connType = 'live';
    } else if (req.url.indexOf('/messages/') === 0) {
        connType = 'messages';
    } else if (req.url.match(/^\/api\/v\d\/query/)) {
        connType = 'api/vx/query';
    }

    // TODO: make a proper routing/versioning middleware for this (see middleware/api.js for rest)
    switch (connType) {
    case 'api/vx/query':
    case 'query':
    case 'live':
    case 'messages': {
        const token = url.parse(req.url, true).query.access_token;

        require('request').get({
            url: `http://${config.user_persistence_server.host}:${config.user_persistence_server.port}/verify`,
            headers: {
                'Content-Type': 'application/json',
                'x-access-token': token
            }
        }, function (error, response, body) {
            if (!error && response.statusCode === 200) {
                if (body && JSON.parse(body).error) {
                    socket.end();
                } else {
                    body = JSON.parse(body);
                    let wsHost = config.query_service.host;
                    let wsPort = config.query_service.port;

                    if (connType === 'live') {
                        wsHost = config.api_server.host;
                        wsPort = config.api_server.port;
                    }

                    if (req.url.startsWith('/query/internal')) {
                        socket.end();
                    } else {
                        req.url = req.url.slice(connType.length + 1);
                        req.headers['x-organization-id'] = body.ActiveOrganizationMembership.organizationId;

                        if (connType === 'messages') {
                            proxy.ws(req, socket, head, {
                                target: {
                                    host: '127.0.0.1',
                                    port: config.wsPort
                                }
                            });

                            return;
                        }

                        if (connType === 'api/vx/query') {
                            req.url = `/analytics${req.url}`;
                        }

                        proxy.ws(req, socket, head, {
                            target: {
                                host: wsHost,
                                port: wsPort
                            }
                        }, function () {
                        });
                    }
                }
            } else {
                socket.end();
            }
        });
        break;
    }
    default:
        break;
    }
});

const expressServer = server.listen(config.httpPort, () => {
    logger.log('info', `Express server listening on port ${config.httpPort}`);
});

expressServer.timeout = 1000 * 60 * 10;