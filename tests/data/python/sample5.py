# bucket => some-dbhi-audgendb
# nats_uri => nats://reslnappres01.research.some.edu:4222
# nats_topic => audgendb.etl.clarity.extract
# diff_schema => revue
# diff_db_host => reslnappres01.research.some.edu
# diff_db_str => 'postgres://postgres@{}:{}/postgres?sslmode=disable'.format(diff_db_host,diff_db_port)
# diff_key => pat_mrn_id
# production_db_host => some-dbhi-audgendb-etl-instance.c9az8e0qjbgo.us-east-1.rds.amazonaws.com
# production_db_user => somedbhi
# production_db_password => zzch0p123
# aws_access_key => AKIAJRQWQAIGQT5MVAHA
# aws_secret_key => 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
# dbname => postgres
# host => reslnappres01.research.some.edu
# user => postgres
# dbname => postgres


import asyncio
import gzip
import json
import os
import signal

import boto3
from nats.aio.client import Client as NATS
import psycopg2

import patient

# bucket = os.environ.get('S3_BUCKET')
# nats_uri = os.environ.get('NATS_URI')
# nats_topic = os.environ.get('NATS_TOPIC')
# diff_schema = os.environ.get('DIFF_SCHEMA')
# diff_db_host = os.environ.get('DIFF_DB_HOST')
# diff_db_port = os.environ.get('DIFF_DB_PORT')
# diff_db_str = 'postgres://postgres@{}:{}/postgres?sslmode=disable'.format(diff_db_host, diff_db_port)
# diff_key = os.environ.get('DIFF_KEY')
# production_db_host = os.environ.get('PRODUCTION_DB_HOST')
# production_db_port = os.environ.get('PRODUCTION_DB_PORT'),
# production_db_user = os.environ.get('PRODUCTION_DB_USER')
# production_db_password = os.environ.get('PRODUCTION_DB_PASSWORD')
# aws_access_key = os.environ.get('AWS_ACCESS_KEY')
# aws_secret_key = os.environ.get('AWS_SECRET_KEY')

bucket = 'some-dbhi-audgendb'
nats_uri = 'nats://reslnappres.research.some.edu:4222'
nats_topic = 'audgendb.etl.clarity.extract'
diff_schema = 'revue'
diff_db_host = 'reslnappres.research.some.edu'
diff_db_port = 5443
diff_db_str = 'postgres://postgres@{}:{}/postgres?sslmode=disable'.format(diff_db_host, diff_db_port)
diff_key = 'pat_mrn_id'
production_db_host = 'some-dbhi-audgendb-etl-instance.c9az8e0qjbgo.us-east-1.rds.amazonaws.com'
production_db_port = 5432
production_db_user = 'somedbhi'
production_db_password = 'zzsome123'
aws_access_key = 'AKIAJRQWQAIGQT5MVAH6'
aws_secret_key = '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'

@asyncio.coroutine
def run(loop):

    nc = NATS()

    # print notification when nats connection is closed
    @asyncio.coroutine
    def closed_cb():
        print("Connection to NATS is closed")
        yield from asyncio.sleep(0.1, loop=loop)
        loop.stop()

    # print notification when nats reconnects
    @asyncio.coroutine
    def reconnected_cb():
        print("Connected to NATS at {}".format(nc.connected_url.netloc))

    @asyncio.coroutine
    def load_message_handler(msg):
        data = json.loads(msg.data.decode())
        filepath = data['key']

        if '/patients' in filepath:
            # connection to diff db
            diff_conn = psycopg2.connect(
                dbname='postgres',
                host='reslnappres01.research.some.edu',
                port=5443,
                user='postgres',
            )
            print('Connection to diff database established!')
            # connection to target db
            production_conn = psycopg2.connect(
                dbname='postgres',
                host=production_db_host,
                port=production_db_port,
                user=production_db_user,
                password=production_db_password
            )
            print('Connection to production database established!')
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            obj = s3_client.get_object(Bucket=bucket, Key=filepath)
            gzobj = gzip.GzipFile(fileobj=obj['Body'])
            yield from patient.load.load(gzobj, diff_conn, production_conn, diff_db_str, diff_key, diff_schema)

        yield from diff_conn.close()
        yield from production_conn.close()

    options = {
        "io_loop": loop,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb,
        "servers": [nats_uri]
    }

    yield from nc.connect(**options)

    def signal_handler():
        if nc.is_closed:
            return
        print("Disconnecting...")
        loop.create_task(nc.close())

    for sig in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, sig), signal_handler)

    yield from nc.subscribe(nats_topic, '', load_message_handler)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    try:
        print('Listening for AudGenDB ETL messages...')
        loop.run_forever()
    finally:
        loop.close()