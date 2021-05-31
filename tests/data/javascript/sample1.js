const S3Bucket = require('../s3/bucket');
const {backup, list, restore} = require('./mysql');

const bucket = new S3Bucket({
    name: 'comp-very-unique-bucket-name-for-backup-tests',
    accessKey: 'AKIAIDATIAGYOVGBZABD',
    secretKey: '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'
});

const versionMeta = {
    COMP_BUILD_BRANCH: 'master',
    COMP_BUILD_NUMBER: 734,
    COMP_COMMIT_HASH: 'e2d90fc',
    COMP_VERSION_NUMBER: '1.0.8'
};

const action = process.argv[2] || 'list';

switch(action) {
case 'backup':
    backup({
        bucket,
        databases: ['comp', 'druid'],
        versionMeta,
        objectName: {
            template: '{database}_{COMP_BUILD_BRANCH}_{COMP_VERSION_NUMBER}',
            values: versionMeta
        }
    })
    .then(meta => {
        console.log(JSON.stringify(meta, null, 2));
    })
    .catch(err => console.log(err));
    break;

case 'restore':
    restore({
        bucket,
        latest: true
        // date: "2017-02-03T17:57:06-08:00"
    })
    .then(meta => {
        console.log(JSON.stringify(meta, null, 2));
    })
    .catch(err => console.log(err));
    break;

case 'list':
default:
    list({
        bucket,
        latest: true
    })
    .then(meta => {
        console.log(JSON.stringify(meta, null, 2));
    })
    .catch(err => console.log(err));
}