# -*- coding: utf-8 -*-
#
# Copyright 2017 dpa-infocom GmbH
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
from livebridge.storages.base import BaseStorage
from livebridge.storages import DummyStorage
from livebridge.components import get_db_client


class MockGenerator:

    def __init__(self, data):
        self.data = data

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self.data.pop()
        except IndexError:
            raise StopAsyncIteration


class DummyStorageTests(asynctest.TestCase):

    async def setUp(self):
        self.dsn = "dummy://"
        params = {"dsn": self.dsn}
        self.client = DummyStorage(**params)

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert issubclass(DummyStorage, BaseStorage) is True

    async def test_get_db_client(self):
        params = {"dsn": "dummy://"}
        db = get_db_client(**params)
        assert type(db) == DummyStorage

        # test singleton
        db2 = get_db_client(**params)
        assert db == db2

    async def test_setup(self):
        res = await self.client.setup()
        assert res is False

    async def test_get_last_updated(self):
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
        res = await self.client.insert_post(**params)
        assert res is True

    async def test_update_post(self):
        params = {"target_id": "target-id",
                  "post_id": "post-id",
                  "source_id": "source-id",
                  "text": "Text",
                  "created": datetime.utcnow(),
                  "sticky": True,
                  "updated": datetime.utcnow(),
                  "target_doc": {"foo": "doc"}}
        res = await self.client.update_post(**params)
        assert res is True

    async def test_update_post_failing(self):
        res = await self.client.update_post(**{})
        assert res is True

    async def test_get_known_posts(self):
        res = await self.client.get_known_posts("foo", "baz")
        assert res == []

    async def test_get_post(self):
        res = await self.client.get_post("target", "post")
        assert res is None

    async def test_delete_post(self):
        res = await self.client.delete_post("target", "post")
        assert res is True

    async def test_get_control(self):
        updated = datetime(2017, 6, 1, 11, 3, 2)
        res = await self.client.get_control(updated=updated)
        assert res is False
