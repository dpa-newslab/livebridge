# -*- coding: utf-8 -*-
#
# Copyright 2016,2017 dpa-infocom GmbH
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
import asyncio
import os
from botocore.exceptions import ClientError
from unittest.mock import MagicMock, call
from livebridge.controller import Controller
from livebridge.controldata import ControlData
from livebridge.controldata.controlfile import ControlFile
from livebridge.bridge import LiveBridge
from livebridge.components import SOURCE_MAP, get_hash
from livebridge import config


class ControllerTests(asynctest.TestCase):

    def setUp(self):
        self.control_file = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        self.config = config
        self.config.AWS = {
            "access_key": "foo",
            "secret_key": "baz",
            "region":  "eu-central-1",
            "sqs_s3_queue": "http://foo-queue",
        }
        self.config.POLL_INTERVAL = 10
        self.config.POLL_CONTROL_INTERVAL = 20
        self.controller = Controller(config=self.config, control_file=self.control_file)

    @asynctest.ignore_loop
    def test_init(self):
        assert self.controller.config== self.config
        assert self.controller.poll_interval == self.config.POLL_INTERVAL
        assert self.controller.check_control_interval == self.config.POLL_CONTROL_INTERVAL
        assert self.controller.control_file == self.control_file
        assert isinstance(self.controller, Controller) == True

    async def shutdown(self):
        await asyncio.sleep(3)
        self.controller.shutdown = True

    async def test_check_control_change(self):
        self.controller.bridges = ["one", "two"]
        self.controller.run = asynctest.CoroutineMock(return_value=True)
        self.controller.control_data = asynctest.MagicMock()
        self.controller.control_data.check_control_change = asynctest.CoroutineMock(return_value=True)
        res = await self.controller.check_control_change()
        assert res == True
        assert  self.controller.run.call_count == 1

    async def test_check_control_change_with_exception(self):
        self.controller.check_control_interval = 2
        self.controller.control_data = asynctest.MagicMock()
        self.controller.control_data.check_control_change = asynctest.CoroutineMock(return_value=False)
        self.controller.sleep = asynctest.CoroutineMock(side_effect=[None, self.shutdown()])
        res = await self.controller.check_control_change()
        assert self.controller.control_data.check_control_change.call_count == 2

    async def test_run(self):
        self.controller.remove_old_bridges = asynctest.CoroutineMock(return_value=True)
        self.controller.add_new_bridges = asynctest.CoroutineMock(return_value=True)
        self.controller.check_control_change = asynctest.CoroutineMock(return_value=True)
        assert self.controller.control_data == None
        await self.controller.run()
        assert self.controller.remove_old_bridges.call_count == 1
        assert self.controller.add_new_bridges.call_count == 1
        assert self.controller.check_control_change.call_count == 1
        assert len(self.controller.tasked) == 1

    async def test_run_failing(self):
        self.controller.remove_old_bridges = asynctest.CoroutineMock(return_value=True)
        self.controller.load_control_data = asynctest.CoroutineMock(side_effect=Exception("load_control_file exception"))
        self.controller.control_file = "/does/not/exist.yaml"
        self.controller.retry_run = asynctest.CoroutineMock(return_value=True)
        assert len(self.controller.tasked) == 0
        assert self.controller.control_data == None
        await self.controller.run()
        assert len(self.controller.tasked) == 1
        assert type(self.controller.tasked[0]) == asyncio.Task
        assert self.controller.load_control_data.called == 1
        assert self.controller.remove_old_bridges.called == 0
        assert self.controller.retry_run.called == 1
        assert self.controller.control_data == None

    async def test_run_failing_reuse_existing_control(self):
        # run with existing control
        self.controller.remove_old_bridges = asynctest.CoroutineMock(return_value=True)
        self.controller.add_new_bridges = asynctest.CoroutineMock(return_value=True)
        self.controller.retry_run = asynctest.CoroutineMock(return_value=True)
        self.controller.check_control_change = asynctest.CoroutineMock(return_value=True)
        assert self.controller.control_data == None
        await self.controller.run()
        assert type(self.controller.control_data) == ControlData
        assert self.controller.remove_old_bridges.call_count == 1
        assert self.controller.add_new_bridges.call_count == 1
        assert self.controller.retry_run.call_count == 0
        assert self.controller.check_control_change.call_count == 1
        assert len(self.controller.tasked) == 1

        # run again with failing control file
        existing_control = self.controller.control_data
        self.controller.load_control_data = asynctest.CoroutineMock(side_effect=Exception("load_control_file exception"))
        await self.controller.run()
        assert len(self.controller.tasked) == 2
        assert self.controller.remove_old_bridges.call_count == 1
        assert self.controller.add_new_bridges.call_count == 1
        assert self.controller.retry_run.call_count == 1
        assert self.controller.control_data == existing_control
        assert self.controller.check_control_change.call_count == 1

    async def test_run_retry(self):
        self.controller.run = asynctest.CoroutineMock()
        self.controller.retry_run_interval = 2
        assert self.controller.control_data == None
        await self.controller.retry_run()
        assert self.controller.run.called
        assert self.controller.run.call_count ==  1

    async def test_clean_shutdown(self):
        # mock bridges
        bridge1 = MagicMock()
        bridge1.check_posts = asynctest.CoroutineMock()
        bridge2 = MagicMock()
        bridge2.check_posts = asynctest.CoroutineMock()

        # run mock bridges
        self.controller.run = asynctest.CoroutineMock()
        self.controller.bridges = {bridge1: bridge1, bridge2: bridge2}
        asyncio.Task(self.controller.run_poller(bridge=bridge1, interval=2))
        asyncio.Task(self.controller.run_poller(bridge=bridge2, interval=2))

        # shutdown
        assert self.controller.shutdown == False
        assert len(self.controller.bridges) == 2
        await self.controller.clean_shutdown()
        assert self.controller.shutdown == True
        assert len(self.controller.bridges) == 0

    async def test_add_new_bridge(self):
        bridge = asynctest.MagicMock()
        self.controller.bridges[bridge] = asynctest.CoroutineMock(return_value=True)()
        self.controller.control_data = asynctest.MagicMock()
        self.controller.control_data.list_new_bridges = MagicMock(return_value=[{"foo": "baz"}, {"bar": "baz"}])
        self.controller.append_bridge = MagicMock(return_value=bridge)
        await self.controller.add_new_bridges()
        assert self.controller.control_data.list_new_bridges.call_count == 1
        assert self.controller.append_bridge.call_count == 2
        assert self.controller.append_bridge.call_args_list == [call({"foo": "baz"}), call({"bar": "baz"})]

    async def test_remove_old_bridges(self):
        bridge1 = asynctest.MagicMock(hash=get_hash({"foo": "baz"}))#, close=MagicMock())
        bridge2 = asynctest.MagicMock(hash=get_hash({"bar": "baz"}))
        self.controller.bridges = {
            bridge1: asynctest.CoroutineMock(return_value=True),
            bridge2: asynctest.CoroutineMock(return_value=True)
        }
        self.controller.control_data = asynctest.MagicMock()
        self.controller.control_data.list_removed_bridges = MagicMock(return_value=[{"foo": "baz"}, {"bar": "baz"}])
        self.controller.remove_bridge = asynctest.CoroutineMock(return_value=True)
        await self.controller.remove_old_bridges()
        assert self.controller.remove_bridge.call_count == 2
        assert self.controller.bridges[bridge1].close.call_count == 1
        assert self.controller.bridges[bridge2].close.call_count == 1
        assert bridge1.stop.call_count == 1
        assert bridge2.stop.call_count == 1

    async def test_run_poller(self):
        # mock coroutine, will set shutdown flag when called
        async def mock_routine():
            self.controller.shutdown = True

        self.controller.sleep = asynctest.CoroutineMock(return_value=True)

        # mock bridge
        bridge1 = MagicMock()
        bridge1.check_posts = mock_routine

        self.controller.bridges = {bridge1: bridge1}

        # run and stop bridge1
        await self.controller.run_poller(bridge=bridge1, interval=2)
        assert self.controller.sleep.call_count == 1

    async def test_run_poller_stopped(self):
        # make some mock bridges
        bridge1 = MagicMock()
        bridge2 = MagicMock()
        bridge1.check_posts = asynctest.CoroutineMock()
        self.controller.bridges = {bridge1: bridge1, bridge2: bridge2}
        self.controller.shutdown = True

        # stop bridge1
        await self.controller.run_poller(bridge=bridge1)
        assert self.controller.bridges.get(bridge1) == None
        assert self.controller.bridges.get(bridge2) == bridge2

        # stop bridge2
        await self.controller.run_poller(bridge=bridge2)
        assert len(self.controller.bridges) == 0

    async def test_run_streaming(self):
        # mock coroutine, will set reread flag when called
        async def stop():
            await asyncio.sleep(2)
            self.controller.shutdown = True

        async def mock_routine():
            asyncio.Task(stop())

        bridge = MagicMock()
        bridge.listen_ws = asynctest.CoroutineMock(side_effect=mock_routine)

        self.controller.remove_bridge = asynctest.CoroutineMock(return_value=True)
        self.controller.shutdown = False
        await self.controller.run_stream(bridge=bridge)
        assert self.controller.remove_bridge.call_count == 1

    async def test_stop_bridges(self):
        sleeper = MagicMock()
        sleeper.cancel = asynctest.CoroutineMock()
        self.controller.sleep_tasks.append(sleeper)
        await self.controller.stop_bridges()
        assert sleeper.cancel.call_count == 1

    async def test_append_streaming_bridge(self):
        class Source:
            mode = "streaming"
            def __init__(self, **kwargs):
                pass
        SOURCE_MAP["liveblog"] = Source
        assert len(self.controller.bridges) == 0
        config = {"mode": "streaming", "type": "liveblog", "targets": [{"type": "scribble"}]}
        self.controller.run_stream = asynctest.CoroutineMock(return_value="foo")
        self.controller.append_bridge(config)
        assert len(self.controller.bridges) == 1
        for bridge in self.controller.bridges.keys():
            assert type(bridge) == LiveBridge
            assert bridge.source.mode == "streaming"

    @asynctest.ignore_loop
    def test_append_poller_bridge(self):
        class Source:
            mode = "polling"
            def __init__(self, **kwargs):
                pass
        SOURCE_MAP["liveblog"] = Source
        assert len(self.controller.bridges) == 0
        config = {"mode": "polling", "type": "liveblog", "targets": [{"type": "scribble"}]}
        self.controller.run_poller = asynctest.CoroutineMock(return_value="foo")
        self.controller.append_bridge(config)
        assert len(self.controller.bridges) == 1
        for bridge in self.controller.bridges.keys():
            assert type(bridge) == LiveBridge
            assert bridge.source.mode == "polling"

    async def test_remove_bridge(self):
        bridge1 = MagicMock(source=MagicMock())
        bridge2 = MagicMock()
        bridge2.source = MagicMock()
        bridge2.source.stop = asynctest.CoroutineMock(return_value=True)
        self.controller.bridges = {bridge1: "foo", bridge2: "baz"}

        # remove bridge 1
        await self.controller.remove_bridge(bridge1)
        assert len(self.controller.bridges) == 1
        assert bridge1 not in self.controller.bridges.keys()
        assert bridge2 in self.controller.bridges.keys()
        assert bridge2.source.stop.call_count == 0

        # remove bridge 2
        await self.controller.remove_bridge(bridge2)
        assert len(self.controller.bridges) == 0
        assert bridge2.source.stop.call_count == 1

    async def test_sleep_cancelled(self):
        with asynctest.patch("asyncio.ensure_future") as mocked_ensure:
            mocked_ensure.return_value = True
            self.controller.sleep_tasks = MagicMock()
            self.controller.sleep_tasks.append = MagicMock(side_effect=[asyncio.CancelledError()])
            res = await self.controller.sleep(3)
            assert res == True

    async def test_sleep_shutdown(self):
        self.controller.shutdown = True
        assert await self.controller.sleep(5) == False

    async def test_save_control_data(self):#, mocked):
        doc = {"foo": "baz"}
        self.controller.control_file =  "/tmp/lb_test_controller_save"
        res = await self.controller.save_control_data(doc)
        assert res == True

        assert os.path.exists(self.controller.control_file) == 1

        f = open(self.controller.control_file)
        assert 'foo: baz\n' == f.read()
        f.close()

        os.remove(self.controller.control_file)
