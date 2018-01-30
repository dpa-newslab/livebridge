# -*- coding: utf-8 -*-
#
# Copyright 2016, 2017 dpa-infocom GmbH
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
from livebridge.base import BaseTarget, InvalidTargetResource
from livebridge.bridge import LiveBridge
from livebridge.components import get_hash


class LiveBridgeTest(asynctest.TestCase):

    def setUp(self):
        self.user = "foo"
        self.password = "bla"
        self.source_id = 12345
        self.endpoint = "https://example.com/api"
        self.label = "Testlabel"
        self.bridge_config = {"auth": {"user": self.user, "password": self.password}, "type": "liveblog",
                              "source_id": self.source_id, "endpoint": self.endpoint,
                              "label": self.label}
        self.bridge = LiveBridge(self.bridge_config)
        self.bridge.api_client = asynctest.MagicMock()
        self.bridge.api_client.last_updated = None
        self.sc = BaseTarget()

    async def test_init(self):
        assert self.bridge.source_id == self.source_id
        assert self.bridge.endpoint == self.endpoint
        assert self.bridge.label == self.label
        assert self.bridge.hash == get_hash(self.bridge_config)
        assert self.bridge.retry_multiplier == 5
        assert self.bridge.max_retries == 10

    async def test_client_init(self):
        assert repr(self.bridge) == "<LiveBridge [Testlabel] https://example.com/api 12345>"

    async def test_add_target(self):
        assert len(self.bridge.targets) == 0
        self.bridge.add_target(self.sc)
        assert len(self.bridge.targets) == 1

    async def test_put_to_queue(self):
        with asynctest.patch("asyncio.ensure_future") as mocked_ensure:
            mocked_ensure.return_value = "test"
            self.bridge._queue_consumer = asynctest.CoroutineMock(return_value="test")
            self.bridge.queue = asynctest.MagicMock()
            self.bridge.queue.put = asynctest.CoroutineMock(return_value=None)
            await self.bridge._put_to_queue({"foo": "baz"})
            assert self.bridge._queue_consumer.call_count == 1
            assert self.bridge.queue.put.call_count == 1
            assert self.bridge.queue_task == "test"

            await self.bridge._put_to_queue({"foo": "baz"})
            assert self.bridge._queue_consumer.call_count == 1
            assert self.bridge.queue.put.call_count == 2
            assert self.bridge.queue_task == "test"

    async def test_stop(self):
        self.bridge.queue_task = asynctest.MagicMock()
        self.bridge.queue_task.cancel = asynctest.CoroutineMock(return_value=None)
        sleep_task = asynctest.MagicMock()
        self.bridge.sleep_tasks.append(sleep_task)
        assert self.bridge.stop() is True
        assert self.bridge.queue_task.cancel.call_count == 1

    async def test_sleep_cancel(self):
        self.loop.call_later(3, self.bridge.stop)
        await self.bridge._sleep(10)

    async def test_action_done_exception(self):
        item_in = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 0
        }
        self.bridge.queue.task_done = asynctest.CoroutineMock(return_value=True)
        future = asynctest.MagicMock(asyncio.Future)
        future.exception = asynctest.Mock(return_value=None)
        await self.bridge._action_done(future, item_in)
        assert self.bridge.queue.task_done.call_count == 1
        assert future.exception.call_count == 1

    async def test_action_done_exception_invalid_target(self):
        item_in = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 0
        }
        self.bridge.queue.task_done = asynctest.CoroutineMock(return_value=True)
        future = asynctest.MagicMock(asyncio.Future)
        future.exception = asynctest.Mock(return_value=InvalidTargetResource("Test"))
        await self.bridge._action_done(future, item_in)
        assert self.bridge.queue.task_done.call_count == 1
        assert future.exception.call_count == 1

    async def test_action_done(self):
        item_in = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 0
        }
        future = asyncio.Future()
        self.bridge.queue.task_done = asynctest.CoroutineMock(return_value=True)
        self.bridge._put_to_queue = asynctest.CoroutineMock(return_value=True)
        future.exception = asynctest.CoroutineMock(return_value=Exception("TestException"))
        await self.bridge._action_done(future, item_in)
        assert item_in["count"] == 1
        assert self.bridge._put_to_queue.call_count == 1
        assert self.bridge._put_to_queue.call_args == asynctest.call(item_in)
        assert self.bridge.queue.task_done.call_count == 1

    async def test_action_done_max_retries(self):
        item_in = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 10
        }
        future = asyncio.Future()
        self.bridge.queue.task_done = asynctest.CoroutineMock(return_value=True)
        self.bridge._sleep = asynctest.CoroutineMock(return_value=True)
        self.bridge._put_to_queue = asynctest.CoroutineMock(return_value=True)
        future.exception = asynctest.CoroutineMock(return_value=Exception("TestException"))
        await self.bridge._action_done(future, item_in)
        assert item_in["count"] == 10
        assert self.bridge._put_to_queue.call_count == 0
        assert self.bridge._sleep.call_count == 0
        assert self.bridge.queue.task_done.call_count == 1

    async def test_process_action(self):
        task = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 0
        }
        task["target"].handle_post = asynctest.CoroutineMock(return_value=True)
        self.bridge._action_done = asynctest.CoroutineMock(return_value=True)
        await self.bridge._process_action(task)
        assert task["target"].handle_post.call_count == 1
        assert task["target"].handle_post.call_args == asynctest.call(task["post"])

    async def test_queue_consumer(self):
        task = {
            "target": asynctest.MagicMock(),
            "post": asynctest.CoroutineMock(return_value=True),
            "count": 0
        }
        self.bridge.queue.get = asynctest.CoroutineMock(side_effect=[task, Exception("Test")])
        self.bridge.queue.task_done = asynctest.CoroutineMock(return_value=True)
        self.bridge._process_action = asynctest.CoroutineMock(return_value=None)
        await self.bridge._queue_consumer()
        self.bridge.queue.get.call_count == 2
        self.bridge._process_action.call_count == 1
        self.bridge.queue.task_done.call_count == 1

    async def test_queue_consumer_aborting(self):
        item = {
            "target": asynctest.MagicMock(),
            "post": asynctest.MagicMock(),
            "count": 11
        }
        self.bridge.queue.get = asynctest.CoroutineMock(side_effect=[item, asyncio.CancelledError()])
        self.bridge._process_action = asynctest.CoroutineMock(return_value=None)
        self.bridge.queue.task_done = asynctest.CoroutineMock()
        await self.bridge._queue_consumer()
        self.bridge._process_action.call_count == 1
        self.bridge.queue.get.call_count == 2
        self.bridge.queue.task_done.call_count == 1

    async def test_check_posts(self):
        self.bridge.new_posts = asynctest.CoroutineMock(return_value=None)
        self.bridge.api_client.poll = asynctest.CoroutineMock(return_value=["one", "two"])
        self.bridge._put_to_queue = asynctest.CoroutineMock(return_value=True)
        res = await self.bridge.check_posts()
        assert res is True
        assert self.bridge.api_client.poll.call_count == 1
        self.bridge.new_posts.assert_called_once_with(["one", "two"])

    async def test_check_posts_empty(self):
        self.bridge.source.get = asynctest.CoroutineMock(side_effect=Exception)
        self.bridge.source.poll = asynctest.CoroutineMock(return_value=False)
        assert self.bridge.source.last_updated is None
        res = await self.bridge.check_posts()
        assert res is True

    async def test_check_posts_failing(self):
        self.bridge.source.poll = asynctest.CoroutineMock(side_effect=Exception)
        assert self.bridge.source.last_updated is None
        res = await self.bridge.check_posts()
        assert res is True

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
        self.bridge._put_to_queue = asynctest.CoroutineMock(return_value=True)

        res = await self.bridge.new_posts([api_res])
        assert res is None
        assert self.bridge._put_to_queue.call_count == 1

    async def test_new_posts_failing(self):
        res = await self.bridge.new_posts(lambda: Exception())
        assert res is None

    async def test_listen_ws(self):
        self.bridge.source.listen = asynctest.CoroutineMock(return_value=None)
        res = await self.bridge.listen_ws()
        assert type(res) == asyncio.Task
        self.bridge.source.listen.assert_called_once_with(self.bridge.new_posts)

    @asynctest.ignore_loop
    def test_get_hash(self):
        assert get_hash({"foo": "bar"}) == "dd63dafcbd4d5b28badfcaf86fb6fcdb"
        assert get_hash([1, 2, 3, 4, 5, 6]) == "199ff5b613f5dc25dff99df513516bf9"
