import pprint
# import pyjsparser
# import requests
# from calmjs.parse import es5
# from calmjs.parse.asttypes import Object, VarDecl, FunctionCall
# from calmjs.parse.walkers import Walker
import esprima
# r = requests.get("http://172.16.18.113:8000/main.1b104cf5.chunk.js")
# data = r.content.decode('utf-8')

data = """const S3Bucket = require('../s3/bucket');
const {backup, list, restore} = require('./mysql');

const bucket = new S3Bucket({
    name: 'netsil-very-unique-bucket-name-for-backup-tests',
    accessKey: 'AKIAIDATIAGYOVGBZVWA',
    secretKey: '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'
});

const versionMeta = {
    NETSIL_BUILD_BRANCH: 'master',
    NETSIL_BUILD_NUMBER: 734,
    NETSIL_COMMIT_HASH: 'e2d90fc',
    NETSIL_VERSION_NUMBER: '1.0.8'
};

const action = process.argv[2] || 'list';

switch(action) {
case 'backup':
    backup({
        bucket,
        databases: ['netsil', 'druid'],
        versionMeta,
        objectName: {
            template: '{database}_{NETSIL_BUILD_BRANCH}_{NETSIL_VERSION_NUMBER}',
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
"""

# program = data
filename = "/home/terryrodery/build.js"
with open(filename, "r", encoding='utf-8') as f:
    program = f.read()
# pprint.pprint(esprima.tokenize(program))
pprint.pprint(esprima.parseScript(program))

# shit = esprima.parseScript(program)

# print("breakpoint")
