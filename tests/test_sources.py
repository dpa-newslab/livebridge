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
from livebridge.base import BaseSource, PollingSource, StreamingSource
from livebridge.storages.base import BaseStorage
from livebridge.components import get_source, add_source

class TestSource(StreamingSource):
    type = "test"
    def __init__(self, *, config={}, **kwargs):
        self.foo = config.get("foo")

class BaseSourcesTest(asynctest.TestCase):

    async def test_base_source(self):
        source = BaseSource()
        db = source._db
        assert isinstance(db, BaseStorage)

    async def test_websocket_methods(self):
        source = StreamingSource()
        with self.assertRaises(NotImplementedError):
            await source.listen(callback="")

        with self.assertRaises(NotImplementedError):
            await source.stop()

    async def test_polling_methods(self):
        source = PollingSource()
        with self.assertRaises(NotImplementedError):
            await source.poll()

    @asynctest.ignore_loop
    def test_get_source(self):
        source = TestSource
        add_source(source)
        conf = {"type": "test", "foo": "baz"}
        new_source = get_source(conf)
        assert new_source.type == conf["type"]
        assert new_source.foo == conf["foo"]

    @asynctest.ignore_loop
    def test_get_source_unkown(self):
        source = get_source({"type": "foo"})
        assert source == None

    async def test_filter_new_posts(self):
        source = BaseSource()
        source._db_client = asynctest.MagicMock()
        source._db_client.get_known_posts = asynctest.CoroutineMock(return_value=["two", "four", "five"])
        post_ids = ["one", "two", "three", "four", "five", "six"]
        new_ids = await source.filter_new_posts("source_id", post_ids)
        assert new_ids == ["one", "three", "six"]
        source._db_client.get_known_posts.assert_called_once_with("source_id", post_ids)

        # empty list
        source._db_client.get_known_posts = asynctest.CoroutineMock(return_value=[])
        new_ids = await source.filter_new_posts("source_id", [])
        assert new_ids == []
        source._db_client.get_known_posts.assert_called_once_with("source_id", [])

    async def test_filter_new_posts_failing(self):
        source = BaseSource()
        source._db_client = asynctest.MagicMock()
        source._db_client.get_known_posts = asynctest.CoroutineMock(side_effect=Exception())
        new_ids = await source.filter_new_posts("source_id", [])
        assert new_ids == []
        source._db_client.get_known_posts.call_count = 1

    async def test_get_last_updated(self):
        source = BaseSource()
        source._db_client = asynctest.MagicMock()
        tstamp = datetime.utcnow()
        source._db_client.get_last_updated = asynctest.CoroutineMock(return_value=tstamp)
        last_updated = await source.get_last_updated("foo")
        assert last_updated == tstamp
        assert source._db_client.get_last_updated.call_count == 1
        assert source._db_client.get_last_updated.call_args == asynctest.call("foo")

        # no data from storage
        source._db_client.get_last_updated = asynctest.CoroutineMock(return_value=None)
        last_updated = await source.get_last_updated("foo")
        assert last_updated == None
