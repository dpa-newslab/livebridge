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
import asyncio
import asynctest
from livebridge.base import BaseTarget
from livebridge.bridge import LiveBridge
from tests import load_json

class LiveBridgeTest(asynctest.TestCase):

    def setUp(self):
        self.user = "foo"
        self.password = "bla"
        self.source_id = 12345
        self.endpoint= "https://example.com/api"
        self.label= "Testlabel"
        self.bridge = LiveBridge({"auth": {"user": self.user, "password": self.password}, "type": "liveblog",
                                 "source_id": self.source_id, "endpoint": self.endpoint,
                                 "label": self.label})
        self.bridge.api_client = asynctest.MagicMock()
        self.bridge.api_client.last_updated = None
        self.sc = BaseTarget()

    @asynctest.ignore_loop
    def test_init(self):
        assert self.bridge.source_id == self.source_id
        assert self.bridge.endpoint == self.endpoint
        assert self.bridge.label == self.label

    @asynctest.ignore_loop
    def test_client_init(self):
        assert repr(self.bridge) == "<LiveBridge [Testlabel] https://example.com/api 12345>"

    @asynctest.ignore_loop
    def test_add_target(self):
        assert len(self.bridge.targets) == 0
        self.bridge.add_target(self.sc)
        assert len(self.bridge.targets) == 1

    async def test_check_posts(self):
        self.bridge.new_posts =  asynctest.CoroutineMock()
        self.bridge.db.get_last_updated = asynctest.CoroutineMock(return_value=None)
        self.bridge.api_client.poll =  asynctest.CoroutineMock(return_value=["one", "two"])
        res = await self.bridge.check_posts()
        assert res == True
        assert self.bridge.api_client.poll.call_count == 1
        self.bridge.db.get_last_updated.assert_called_once_with(12345)
        self.bridge.new_posts.assert_called_once_with(["one", "two"])

    async def test_check_posts_empty(self):
        self.bridge.source.get = asynctest.CoroutineMock(side_effect=Exception)
        assert self.bridge.source.last_updated == None
        self.bridge.db.get_last_updated = asynctest.CoroutineMock(return_value=None)
        res = await self.bridge.check_posts()
        assert res == True
        assert self.bridge.source.last_updated == None
        assert self.bridge.db.get_last_updated.call_count == 1

    async def test_check_posts_failing(self):
        self.bridge.source.poll = asynctest.CoroutineMock(side_effect=Exception)
        assert self.bridge.source.last_updated == None
        self.bridge.db.get_last_updated = asynctest.CoroutineMock(return_value=None)
        res = await self.bridge.check_posts()
        assert res == True
        assert self.bridge.source.last_updated == None
        assert self.bridge.db.get_last_updated.call_count == 1

    async def test_new_posts(self):
        # return of target
        handle_res = asynctest.MagicMock()
        handle_res.id = "654321"
        handle_res.target_doc = {"foo": "baz"}

        # target
        target = asynctest.MagicMock()
        target.handle_post = asynctest.CoroutineMock(return_value=handle_res)
        target.type = "scribble"
        target.target_id = "foo"

        # post
        post = asynctest.MagicMock()
        post.id = "12345"
        self.bridge.targets.append(target)

        # mock method calls
        api_res = asynctest.MagicMock()
        api_res.updated = "2016-10-31T10:10:10+0:00"

        # test one
        res = await self.bridge.new_posts([api_res])
        assert res == True

    async def test_new_posts_failing(self):
        res = await self.bridge.new_posts(lambda: Exception())
        assert res == True

    async def test_listen_ws(self):
        self.bridge.source.listen = asynctest.CoroutineMock()
        res = await self.bridge.listen_ws()
        assert type(res) == asyncio.Task
        self.bridge.source.listen.assert_called_once_with(self.bridge.new_posts)
