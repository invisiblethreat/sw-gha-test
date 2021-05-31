const express = require('express');
const listMiddleware = require('./list');
const createMiddleware = require('./create');
const restoreMiddleware = require('./restore');
const scheduleMiddleware = require('./schedule');
const updateConfigMiddleware = require('./updateConfig');
const routes = express.Router();

const getSettings = require('../../lib/util/settings');

const {
    BACKUP_S3_BUCKET: bucketName = '<s3_bucket_name>',
    BACKUP_S3_ACCESS_KEY: accessKey = '<s3_access_key>',
    BACKUP_S3_SECRET_KEY: secretKey = '<s3_secret_key>',
    COMP_BUILD_BRANCH,
    COMP_BUILD_NUMBER,
    COMP_COMMIT_HASH,
    COMP_VERSION_NUMBER,
    MYSQL_HOST,
    MYSQL_PORT
} = process.env;

const versionMeta = {
    COMP_BUILD_BRANCH,
    COMP_BUILD_NUMBER,
    COMP_COMMIT_HASH,
    COMP_VERSION_NUMBER
};

getSettings.fetch()
    .then(function(partialConfig) {
        if (partialConfig === undefined) {
            partialConfig = {
                backup: {},
                storage: {}
            }
        }

    /*
    backup: {
        schedule: {
            minute: '*',
            hour: '*',
            day: '*',
            month: '*',
            week: '*',
            macro: ''
        }
    },
    storage : {
        type: 's3'
        properties: {
            storageBucket: '',
            s3Endpoint: '',
            accessKey: '',
            secretKey: ''
        }
    },
    */
    const config = {
        mysql: {
            host: MYSQL_HOST || '127.0.0.1',
            port: MYSQL_PORT || 3306,
            databases: ['comp', 'druid']
        },
        backup: partialConfig.backup,
        storage: partialConfig.storage,
        versionMeta: versionMeta,
        objectName: {
            template: '{database}_{COMP_BUILD_BRANCH}_{COMP_VERSION_NUMBER}',
            values: versionMeta
        },
        gzip: true,
        time: undefined
    };

    const list = listMiddleware(config);
    const create = createMiddleware(config);
    const restore = restoreMiddleware(config);
    const schedule = scheduleMiddleware(config);
    const updateConfig = updateConfigMiddleware(config);

    routes.get('/backup(/latest)?', list);
    routes.get('/config', updateConfig.get);
    routes.get('/status', (req, res) => res.send('OK'));
    //routes.get('/schedule', schedule);

    routes.post('/backup', create);
    routes.post('/config', updateConfig.post);
    routes.post('/restore', restore);
    //routes.post('/schedule', schedule);
}).catch(function (err) {
    console.log(err.stack || err);
    process.exit();
});

module.exports = routes;