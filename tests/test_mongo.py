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
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection, AsyncIOMotorCursor
from livebridge.storages.base import BaseStorage
from livebridge.storages import MongoStorage
from livebridge.components import get_db_client


class MockGenerator:

    def __init__(self, data):
        self.data = data

    async def next_data(self):
        return self.data.pop()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.next_data()
        except IndexError:
            raise StopAsyncIteration


class MongoStorageTests(asynctest.TestCase):

    async def setUp(self):
        self.dsn = "mongodb://192.168.2.1:2107/foobaz"
        self.table_name = "test_coll"
        self.control_table_name = "test_control_coll"
        params = {"dsn": self.dsn, "table_name": self.table_name, "control_table_name": self.control_table_name}
        self.client = MongoStorage(**params)
        self.target_id = "scribble-max.mustermann@dpa-info.com-1234567890"

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert self.client.dsn == self.dsn
        assert self.client.table_name == self.table_name
        assert issubclass(MongoStorage, BaseStorage) is True

    async def test_db(self):
        db = await self.client.db
        assert type(db) == AsyncIOMotorDatabase

        self.client._db = "foo"
        db = await self.client.db
        assert db == "foo"

    async def test_get_db_client(self):
        params = {
            "dsn": "mongodb://127.0.0.1:21027/foo",
            "table_name": "lb_test"
        }
        db = get_db_client(**params)
        assert type(db) == MongoStorage
        assert db.dsn == params["dsn"]
        assert db.db_name == "foo"
        assert db.table_name == params["table_name"]

        # test singleton
        db2 = get_db_client(**params)
        assert db == db2

    async def test_setup(self):
        self.client._db = asynctest.MagicMock()
        self.client._db.list_collection_names = asynctest.CoroutineMock(
            return_value=[self.table_name, self.control_table_name])
        self.client._db.create_collection = asynctest.CoroutineMock(return_value=True)
        self.client._db[self.table_name].create_index = asynctest.CoroutineMock(return_value=True)
        res = await self.client.setup()
        assert res is False
        assert self.client._db.create_collection.call_count == 0
        assert self.client._db[self.table_name].create_index.call_count == 0

        self.client._db.list_collection_names = asynctest.CoroutineMock(return_value=[self.control_table_name])
        res = await self.client.setup()
        assert res is True
        assert self.client._db.create_collection.call_count == 1
        assert self.client._db[self.table_name].create_index.call_count == 1

        self.client._db.list_collection_names = asynctest.CoroutineMock(return_value=[self.table_name])
        res = await self.client.setup()
        assert res is True
        assert self.client._db.create_collection.call_count == 2
        assert self.client._db[self.table_name].create_index.call_count == 1

        self.client._db.list_collection_names = asynctest.CoroutineMock(return_value=[])
        res = await self.client.setup()
        assert res is True
        assert self.client._db.create_collection.call_count == 4
        assert self.client._db[self.table_name].create_index.call_count == 2

    async def test_setup_failing(self):
        self.client._db = asynctest.MagicMock()
        self.client._db.list_collection_names = asynctest.CoroutineMock(side_effect=Exception("Test-Error"))
        res = await self.client.setup()
        assert res is False

    async def test_get_last_updated(self):
        item = {"updated": datetime.strptime("2016-10-19T10:13:43+00:00", "%Y-%m-%dT%H:%M:%S+00:00")}
        cursor = MockGenerator([item])
        cursor.sort = asynctest.MagicMock(spec=AsyncIOMotorCursor)
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find.return_value = cursor
        self.client._db = {self.table_name: coll}
        res = await self.client.get_last_updated("source")
        assert type(res) == datetime
        assert (res.year, res.month, res.second) == (2016, 10, 43)
        assert coll.find.call_count == 1
        assert coll.find.call_args == asynctest.call({'source_id': 'source'})
        assert cursor.sort.call_count == 1
        assert cursor.sort.return_value.limit.call_count == 1

        # no date
        cursor.data = []
        res = await self.client.get_last_updated("source")
        assert res is None

    async def test_get_last_updated_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find.side_effect = Exception("Test-Error")
        self.client._db = {self.table_name: coll}
        res = await self.client.get_last_updated("source")
        assert res is None

    async def test_insert_post(self):
        params = {"target_id": "target-id",
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "created": "2016-10-19T10:13:43+00:00",
                  "sticky": True,
                  "updated": "2016-10-19T10:13:43+00:00",
                  "target_doc": {"foo": "doc"}}
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.insert_one = asynctest.CoroutineMock(return_value=True)
        self.client._db = {self.table_name: coll}
        res = await self.client.insert_post(**params)
        assert res is True
        assert coll.insert_one.call_count == 1
        assert coll.insert_one.call_args[0][0]["created"] == params["created"]
        assert coll.insert_one.call_args[0][0]["sticky"] == "1"

        # failing
        coll.insert_one.side_effect = Exception("Test-Error")
        res = await self.client.insert_post(**params)
        assert res is False

    async def test_update_post(self):
        params = {"target_id": "target-id",
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "created": datetime.utcnow(),
                  "sticky": True,
                  "updated": datetime.utcnow(),
                  "target_doc": {"foo": "doc"}}
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.replace_one = asynctest.CoroutineMock(return_value=True)
        self.client._db = {self.table_name: coll}
        res = await self.client.update_post(**params)
        assert res is True
        assert coll.replace_one.call_count == 1
        assert coll.replace_one.call_args[0][0]["target_id"] == params["target_id"]
        assert coll.replace_one.call_args[0][0]["post_id"] == params["post_id"]
        assert coll.replace_one.call_args[0][1]["created"] == params["created"]
        assert coll.replace_one.call_args[0][1]["sticky"] == "1"

    async def test_update_post_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.replace_one.side_effect = Exception()
        self.client._db = {self.table_name: coll}
        res = await self.client.update_post(**{})
        assert res is False
        assert coll.replace_one.call_count == 1

    async def test_get_known_posts(self):
        source_id = "source-id"
        post_ids = [b"oneoneoneone", b"twotwotwotwo", b"threethreeth", b"fourfourfour",
                    b"fivefivefive", b"sixsixsixsix"]
        cursor = MockGenerator([{"_id": "twotwotwotwo"}, {"_id": "fourfourfourfour"}, {"_id": "sixsixsixsix"}])
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find.return_value = cursor
        self.client._db = {self.table_name: coll}
        res = await self.client.get_known_posts(source_id, post_ids)
        assert res == ['sixsixsixsix', 'fourfourfourfour', 'twotwotwotwo']
        assert coll.find.call_count == 1
        assert coll.find.call_args[0][0]["source_id"] == source_id
        assert type(coll.find.call_args[0][0]["_id"]["$in"]) == list
        assert len(coll.find.call_args[0][0]["_id"]["$in"]) == 6
        assert type(coll.find.call_args[0][0]["_id"]["$in"][0]) == ObjectId

    async def test_get_known_posts_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find.side_effect = Exception("Test-Error")
        self.client._db = {self.table_name: coll}
        res = await self.client.get_known_posts("source-id", [b"oneoneoneone"])
        assert res == []

    async def test_get_post(self):
        item = {
            "_id": ObjectId(b"012345678901"),
            "updated": datetime.strptime("2016-10-19T10:13:43+00:00", "%Y-%m-%dT%H:%M:%S+00:00"),
            "target_doc": {"target": "doc"}
        }
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find_one = asynctest.CoroutineMock(return_value=item)
        self.client._db = {self.table_name: coll}
        res = await self.client.get_post("target", "post")
        assert res["target_doc"] == {'target': 'doc'}
        assert res["updated"] == item["updated"]

    async def test_get_post_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find_one.side_effect = Exception("Test-Error")
        self.client._db = {self.table_name: coll}
        res = await self.client.get_post("target", "post")
        assert res is None

    async def test_delete_post(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.delete_one = asynctest.CoroutineMock(return_value=True)
        self.client._db = {self.table_name: coll}
        res = await self.client.delete_post("target", "post")
        assert res is True
        assert coll.delete_one.call_count == 1
        assert coll.delete_one.call_args[0][0]["target_id"] == "target"
        assert coll.delete_one.call_args[0][0]["post_id"] == "post"

    async def test_delete_post_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.delete_one.side_effect = Exception("Test-Error")
        self.client._db = {self.table_name: coll}
        res = await self.client.delete_post("target", "post")
        assert res is False
        assert coll.delete_one.call_count == 1

    async def test_get_control(self):
        updated = datetime(2017, 6, 1, 11, 3, 2)
        item = {
            'updated': datetime(2017, 6, 1, 11, 3, 1),
            'data': {"bridges": [{"foo": "bar"}], "auth": {"foo": "baz"}},
            '_id': ObjectId(b"012345678901"), 'type': 'control'}
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find_one = asynctest.CoroutineMock(return_value=item)
        self.client._db = {self.control_table_name: coll}
        res = await self.client.get_control(updated=updated)
        assert res["data"]["auth"] == {"foo": "baz"}
        assert res["data"]["bridges"] == [{"foo": "bar"}]
        assert res["updated"] == item["updated"]
        assert coll.find_one.call_count == 1
        assert coll.find_one.call_args[0][0]["type"] == "control"

    async def test_get_control_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.find_one.side_effect = Exception("Test-Error")
        self.client._db = {self.control_table_name: coll}
        res = await self.client.get_control()
        assert res is False

    async def test_get_control_failing_with_tstamp(self):
        res = await self.client.get_control(updated="string")
        assert res is False

    async def test_save_control(self):
        data = {"foo": "bar"}
        update_res = asynctest.MagicMock(spec="pymongo.results.UpdateResult", modified_count=1, upserted_id=None)
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.replace_one = asynctest.CoroutineMock(return_value=update_res)
        self.client._db = {self.control_table_name: coll}
        res = await self.client.save_control(data)
        assert res is True
        assert coll.replace_one.call_count == 1
        assert coll.replace_one.call_args[0][1]["data"] == data
        assert coll.replace_one.call_args[0][0] == {"type": "control"}
        assert coll.replace_one.call_args[1] == {"upsert": True}

        # replace operation fails
        update_res.modified_count = 0
        res = await self.client.save_control(data)
        assert res is False

    async def test_save_control_failing(self):
        coll = asynctest.MagicMock(spec=AsyncIOMotorCollection)
        coll.replace_one.side_effect = Exception("Test-Error")
        self.client._db = {self.control_table_name: coll}
        res = await self.client.save_control(data={"foo": "baz"})
        assert res is False
