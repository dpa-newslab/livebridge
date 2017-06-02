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
import os
from datetime import datetime
from sqlalchemy_aio.engine import AsyncioEngine, AsyncioResultProxy, AsyncioConnection
from livebridge.storages.base import BaseStorage
from livebridge.storages import SQLStorage
from livebridge.components import get_db_client


class SQLStorageTests(asynctest.TestCase):

    async def setUp(self):
        self.dsn = "sqlite:///tests/tests.db"
        self.table_name = "test_table"
        self.control_table_name = "test_control_table"
        params = {"dsn": self.dsn, "table_name": self.table_name, "control_table_name": self.control_table_name}
        self.client = SQLStorage(**params)
        self.target_id = "scribble-max.mustermann@dpa-info.com-1234567890"

    async def tearDown(self):
        if os.path.exists("./tests/tests.db"):
            os.remove("./tests/tests.db")

    @asynctest.ignore_loop
    def test_init(self):
        assert self.client.dsn == self.dsn
        assert self.client.table_name == self.table_name
        assert issubclass(SQLStorage, BaseStorage) == True

    async def test_db(self):
        db = await self.client.db
        assert type(db) == AsyncioEngine

    async def test_get_db_client(self):
        params = {
            "dsn": "sqlite:///",
            "table_name": "lb_test"
        }
        db = get_db_client(**params)
        assert type(db) == SQLStorage
        assert db.dsn == params["dsn"]
        assert db.table_name == params["table_name"]

        # test singleton
        db2 = get_db_client(**params)
        assert db == db2

    async def test_setup(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.has_table = asynctest.CoroutineMock(return_value=False)
        self.client._engine.execute = asynctest.CoroutineMock(return_value=True)
        conn = asynctest.MagicMock(spec=AsyncioConnection)
        conn.execute = asynctest.CoroutineMock(return_value=True)
        conn.close = asynctest.CoroutineMock(return_value=True)
        self.client._engine.connect = asynctest.CoroutineMock(return_value=conn)
        res = await self.client.setup()
        assert res == True
        assert conn.execute.call_count == 2

    async def test_setup_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.has_table = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.setup()
        assert res == False

    async def test_get_last_updated(self):
        item = {"updated": datetime.strptime("2016-10-19T10:13:43+00:00", "%Y-%m-%dT%H:%M:%S+00:00")}
        db_res = asynctest.MagicMock(spec=AsyncioResultProxy)
        db_res.first = asynctest.CoroutineMock(return_value=item)
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=db_res)
        res = await self.client.get_last_updated("source")
        assert type(item["updated"]) == datetime
        assert res.year == 2016
        assert res.month ==  10
        assert res.second == 43
        assert self.client._engine.execute.call_count == 1

        # no date
        db_res.first = asynctest.CoroutineMock(return_value={})
        res = await self.client.get_last_updated("source")
        assert res == None

    async def test_get_last_updated_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.get_last_updated("source")
        assert res == None

    async def test_insert_post(self):
        params = {"target_id": "target-id",
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "created": "2016-10-19T10:13:43+00:00",
                  "sticky": True,
                  "updated": "2016-10-19T10:13:43+00:00",
                  "target_doc": {"foo": "doc"}}
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=True)
        res = await self.client.insert_post(**params)
        assert res == True

        # failing
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.insert_post(**params)
        assert res == False

    async def test_update_post(self):
        params = {"target_id": "target-id",
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "created": datetime.utcnow(),
                  "sticky": True,
                  "updated":  datetime.utcnow(),
                  "target_doc": {"foo": "doc"}}
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=True)
        res = await self.client.update_post(**params)
        assert res == True
        assert self.client._engine.execute.call_count == 1

    async def test_update_post_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.update_post(**{})
        assert res == False
        assert self.client._engine.execute.call_count == 1

    async def test_get_known_posts(self):
        source_id =  "source-id"
        post_ids = ["one", "two", "three", "four", "five", "six"]
        db_res = asynctest.MagicMock(spec=AsyncioResultProxy)
        db_res.fetchall = asynctest.CoroutineMock(return_value=[("one",), ("three",), ("five",)])
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=db_res)
        res = await self.client.get_known_posts(source_id, post_ids)
        assert res == ["one", "three", "five"]

    async def test_get_known_posts_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.get_known_posts("source-id", ["one"])
        assert res == []

    async def test_get_post(self):
        item = {
            "updated": datetime.strptime("2016-10-19T10:13:43+00:00", "%Y-%m-%dT%H:%M:%S+00:00"),
            "target_doc": '{"target":"doc"}'
        }
        db_res = asynctest.MagicMock(spec=AsyncioResultProxy)
        db_res.first = asynctest.CoroutineMock(return_value=item)
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=db_res)
        res = await self.client.get_post("target", "post")
        assert res["target_doc"] == {'target': 'doc'}
        assert res["updated"] == item["updated"]

    async def test_get_post_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.get_post("target", "post")
        assert res == None

    async def test_delete_post(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=True)
        res = await self.client.delete_post("target", "post")
        assert res == True

    async def test_delete_post_failing(self):
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.delete_post("target", "post")
        assert res == False

    async def test_get_control(self):
        updated = datetime(2017, 6, 1, 11, 3, 2)
        db_item = {
            'updated': datetime(2017, 6, 1, 11, 3, 1),
            'data': '{"bridges": [{"foo": "bar"}], "auth": {"foo": "baz"}}', 'id': 1, 'type': 'control'}
        db_res = asynctest.MagicMock(spec=AsyncioResultProxy)
        db_res.first = asynctest.CoroutineMock(return_value=db_item)
        self.client._engine = asynctest.MagicMock()
        self.client._engine.execute = asynctest.CoroutineMock(return_value=db_res)
        res = await self.client.get_control(updated=updated)
        assert res["data"]["auth"] ==  {"foo": "baz"}
        assert res["data"]["bridges"] == [{"foo": "bar"}]
        assert self.client._engine.execute.call_count == 1

    async def test_get_control_failing(self):
        db = await self.client.db
        db.execute = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.client.get_control()
        assert res == False

    async def test_get_control_failing_with_tstamp(self):
        res = await self.client.get_control(updated="string")
        assert res == False
