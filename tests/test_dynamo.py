# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asynctest
from datetime import datetime
from botocore.exceptions import ParamValidationError, BotoCoreError
from livebridge.storages.base import BaseStorage
from livebridge.storages import DynamoClient
from livebridge.components import get_db_client
from tests import load_json

class DynamoClientTests(asynctest.TestCase):

    def setUp(self):
        self.access_key = "bla"
        self.secret_key= "bla"
        self.region = "eu-central-1"
        self.table_name= "livebridge_test"
        self.control_table_name= "livebridge_test_control"
        self.endpoint_url= "http://172.17.0.1:8000"
        params = {"access_key":self.access_key,
                  "secret_key": self.secret_key,
                  "region": self.region,
                  "endpoint_url": self.endpoint_url,
                  "table_name": self.table_name,
                  "control_table_name": self.control_table_name}
        DynamoClient._instance = None
        self.client = DynamoClient(**params)
        self.target_id = "scribble-max.mustermann@dpa-info.com-1234567890"

    def tearDown(self):
        self.client.__del__()

    @asynctest.ignore_loop
    def test_init(self):
        assert self.client.access_key == self.access_key
        assert self.client.secret_key == self.secret_key
        assert self.client.region == self.region
        assert self.client.endpoint_url == self.endpoint_url
        assert self.client.table_name == self.table_name
        assert issubclass(DynamoClient, BaseStorage) == True

    async def test_db(self):
        db = await self.client.db
        assert str(db.__class__) == "<class 'aiobotocore.client.DynamoDB'>"
        assert hasattr(db, "list_tables")

    async def test_setup(self):
        self.client.db_client = asynctest.MagicMock()
        table_resp = {"TableNames": []}
        self.client.db_client.list_tables = asynctest.CoroutineMock(return_value=table_resp)
        create_resp = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        self.client.db_client.create_table = asynctest.CoroutineMock(return_value=create_resp)
        res = await self.client.setup()
        assert res == True
        assert self.client.db_client.list_tables.call_count == 1
        assert self.client.db_client.create_table.call_count == 2

        # table exists already
        table_resp = {"TableNames": [self.table_name, self.control_table_name]}
        self.client.db_client.list_tables.return_value = table_resp
        res = await self.client.setup()
        assert res == False
        assert self.client.db_client.list_tables.call_count == 2
        assert self.client.db_client.create_table.call_count == 2

        # failes with exception
        self.client.db_client.list_tables.side_effect = Exception
        res = await self.client.setup()
        assert res == False

    @asynctest.ignore_loop
    def test_singleton_db(self):
        db1 = get_db_client()
        db2 = get_db_client()
        assert db1 == db2
        assert type(db1) == DynamoClient

    async def test_scan(self):
        api_res = {'ScannedCount': 1,
                   'Count': 1,
                   'ResponseMetadata': {
                        'HTTPStatusCode': 200,
                        'RequestId': '7ac4f921-a03b-42ce-85ce-3276f6f93e17'
                    },
                    'Items': [
                        {'attemps': {'N': '1'},
                         'id': {'S': 'urn:newsml:localhost:2016-04-01T15:01:37.662911:e8146c8d-7f5b-4bc9-b21d-9650064c567c'},
                         'source_id': {'S': '56fceedda505e600f71959c8'},
                         'doc': {'S': '{"foo": "bla"}'},
                         'scribbled': {'S': '2016-04-01T15:02:37+00:00'},
                         'date': {'S': '2016-04-01T15:01:37+00:00'}
                        }
                    ]}
        db = await self.client.db
        db.scan =  asynctest.CoroutineMock(return_value=api_res)
        items = await self.client.scan()
        assert type(items) == list
        for p in api_res["Items"][0]:
            assert items[0][p] == api_res["Items"][0][p]
        db.scan.assert_called_once_with(Limit=5, Select="ALL_ATTRIBUTES", TableName="livebridge_test")

    async def test_scan_invalid(self):
        db = await self.client.db
        db.scan = asynctest.CoroutineMock(side_effect=ParamValidationError(report="Exception raised"))
        res = await self.client.scan()
        db.scan.assert_called_once_with(Limit=5, Select="ALL_ATTRIBUTES", TableName="livebridge_test")
        assert res == []

    async def test_insert_post(self):
        api_res = {'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'd92c4314-439a-4bc7-90f5-125a615dfaa2'}}
        db = await self.client.db
        db.put_item =  asynctest.CoroutineMock(return_value=api_res)
        date = datetime.utcnow()
        date_str = datetime.strftime(date, self.client.date_fmt)
        kwargs = {"target_id": "target-id", 
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "sticky": True,
                  "created": date,
                  "updated": date,
                  "target_doc": {"foo": "doc"}}
        res = await self.client.insert_post(**kwargs)
        assert res == True
        assert type(res) == bool
        db.put_item.assert_called_once_with(
            Item={
                'source_id': {'S': 'source-id'},
                'text': {'S': 'Text'},
                'target_id': {'S': 'target-id'},
                'post_id': {'S': 'post-id'},
                'created': {'S': date_str},
                'updated': {'S': date_str},
                'target_doc': {'S': '{"foo": "doc"}'},
                'sticky': {'N': '1'}},
            TableName='livebridge_test')

        # insert_post failing(self):
        db.put_item =  asynctest.CoroutineMock(side_effect=ParamValidationError(report="Exception raised"))
        res = await self.client.insert_post(**kwargs)
        assert res == False
        assert type(res) == bool

    async def test_update_post(self):
        self.client.delete_post = asynctest.CoroutineMock(return_value=True)
        self.client.insert_post = asynctest.CoroutineMock(return_value=True)
        kwargs = {"target_id": "target-id", "post_id": "post-id"}
        res = await self.client.update_post(**kwargs)
        assert res == True
        assert type(res) == bool
        self.client.delete_post.assert_called_once_with('target-id', 'post-id')
        self.client.insert_post.assert_called_once_with(target_id="target-id", post_id="post-id")

    async def test_update_post_failing(self):
        self.client.delete_post = asynctest.CoroutineMock(return_value=False)
        self.client.insert_post = asynctest.CoroutineMock(return_value=True)
        kwargs = {"target_id": "target-id", "post_id": "post-id"}
        res = await self.client.update_post(**kwargs)
        assert res == False
        assert self.client.delete_post.call_count == 1
        assert self.client.insert_post.call_count == 0

        self.client.delete_post = asynctest.CoroutineMock(side_effect=Exception)
        res = await self.client.update_post(**kwargs)
        assert res == False
        assert self.client.delete_post.call_count == 1
        assert self.client.insert_post.call_count == 0

    async def test_get_last_updated(self):
        api_res = load_json("last_updated.json")
        source_id =  "56fceedda505e600f71959c8"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.get_last_updated(source_id)
        assert type(res) == datetime
        assert res.year == 2016
        assert res.month ==  4
        assert res.second == 38
        db.query.assert_called_once_with(
            ExpressionAttributeValues={':value': {'S': '56fceedda505e600f71959c8'}},
            IndexName='source_id-updated-index',
            KeyConditionExpression='source_id = :value',
            Limit=1, ProjectionExpression='source_id, updated, post_id',
            ScanIndexForward=False,
            TableName='livebridge_test')

    async def test_get_last_updated_failing(self):
        source_id =  "56fceedda505e600f71959c8"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(side_effect=BotoCoreError)
        res = await self.client.get_last_updated(source_id)
        assert res == None

    async def test_get_no_last_updated(self):
        api_res = {"Count": 0,
                   "ScannedCount": 0,
                   "Items": [],
                   "ResponseMetadata": {
                        "RequestId": "f0f134f5-413b-41e0-947b-4b515287812d",
                        "HTTPStatusCode": 200
                   }}
        source_id =  "foobla-baz"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.get_last_updated(source_id)
        assert res == None
        assert db.query.call_count == 1

    async def test_get_known_posts(self):
        source_id =  "source-id"
        post_ids = ["one", "two", "three", "four", "five", "six"]
        db_res = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "Items": [
                {"post_id": {"S": "one"}},
                {"post_id": {"S": "three"}},
                {"post_id": {"S": "five"}},
            ]}
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=db_res)
        res = await self.client.get_known_posts(source_id, post_ids)
        assert res == ["one", "three", "five"]
        db.query.assert_called_once_with(
            ExpressionAttributeValues={
                    ':post_id_1': {'S': 'two'}, ':post_id_2': {'S': 'three'}, ':post_id_0': {'S': 'one'},
                    ':value': {'S': 'source-id'}, ':post_id_5': {'S': 'six'}, ':post_id_3': {'S': 'four'},
                    ':post_id_4': {'S': 'five'}},
            FilterExpression='post_id= :post_id_0 OR post_id= :post_id_1 OR post_id= :post_id_2 OR post_id='\
                             +' :post_id_3 OR post_id= :post_id_4 OR post_id= :post_id_5',
            IndexName='source_id-updated-index',
            KeyConditionExpression='source_id = :value ',
            ProjectionExpression='post_id',
            ScanIndexForward=False,
            TableName='livebridge_test')

    async def test_get_known_posts_failing(self):
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.get_known_posts("source-id", ["one"])
        assert res == []

    async def test_get_post(self):
        api_res = {'Count': 1, 'ScannedCount': 2, 'Items': [
                    {'post_id': {'S': 'urn:newsml:localhost:2016-04-06T14:36:37.255055:f2266f58-1e5c-4021-85af-e39087d94372'},
                     'target_id': {'S': self.target_id},
                     'updated': {'S': '2016-04-06T14:36:37+00:00'}}
                ], 'ResponseMetadata': {'RequestId': '80cc148b-16d2-4dbc-813d-a7a3cd17acd5', 'HTTPStatusCode': 200}}
        target_id =  "56fceedda505e600f71959c8"
        post_id = "urn:newsml:localhost:2016-04-06T14:36:37.255055:f2266f58-1e5c-4021-85af-e39087d94372"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.get_post(self.target_id, post_id)
        assert res["target_id"] == self.target_id
        assert res["post_id"] == post_id
        db.query.assert_called_once_with(
            ExpressionAttributeValues={
                ':value': {'S': 'scribble-max.mustermann@dpa-info.com-1234567890'},
                ':post_id': {'S': 'urn:newsml:localhost:2016-04-06T14:36:37.255055:f2266f58-1e5c-4021-85af-e39087d94372'}},
            KeyConditionExpression='target_id = :value AND post_id= :post_id',
            ProjectionExpression='target_id, source_id, updated, post_id, target_doc, sticky',
            ScanIndexForward=False,
            TableName='livebridge_test')

    async def test_get_post_failing(self):
        post_id = "urn:newsml:localhost:2016-04-06T14:36:37.255055:f2266f58-1e5c-4021-85af-e39087d94372"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(side_effect=BotoCoreError)
        res = await self.client.get_post(self.target_id, post_id)
        assert res == None

    async def test_get_post_empty(self):
        api_res = {}
        source_id =  "56fceedda505e600f71959c8"
        post_id = "baz"
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.get_post(source_id, post_id)
        assert res == None

    async def test_delete_post(self):
        api_res = {'ResponseMetadata': {'RequestId': '91c99f7c-cbbe-44d2-bcc8-fcc274043239', 'HTTPStatusCode': 200}}
        db = await self.client.db
        db.delete_item = asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.delete_post("target-id", "baz")
        assert res == True

    async def test_delete_failing(self):
        post_id = "urn:newsml:localhost:2016-04-06T14:36:37.255055:f2266f58-1e5c-4021-85af-e39087d94372"
        db = await self.client.db
        db.delete_item = asynctest.CoroutineMock(side_effect=BotoCoreError)
        res = await self.client.delete_post("target-id", "baz")
        assert res == False

    async def test_get_control(self):
        api_res = {'Count': 1, 'ScannedCount': 1, 'Items': [
                    {'id': {'S': 'control'}, 'data': {'S': '{"bridges": [{"foo": "bla"}], "auth": {"foo": "baz"}}'}}
                ], 'ResponseMetadata': {'RequestId': '80cc148b-16d2-4dbc-813d-a7a3cd17acd5', 'HTTPStatusCode': 200}}
        db = await self.client.db
        db.query =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client.get_control()
        assert res["auth"] ==  {"foo": "baz"}
        assert res["bridges"] == [{"foo": "bla"}]
        db.query.assert_called_once_with(
            ExpressionAttributeValues={':value': {'S': 'control'}},
            KeyConditionExpression='id= :value',
            ScanIndexForward=False,
            TableName='livebridge_test_control')

    async def test_get_control_failing(self):
        db = await self.client.db
        db.query = asynctest.CoroutineMock(side_effect=BotoCoreError)
        res = await self.client.get_control()
        assert res == False
