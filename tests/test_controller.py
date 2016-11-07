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
import asyncio
import os
from unittest.mock import MagicMock
from livebridge.controller import Controller
from livebridge.controlfile import ControlFile
from livebridge.bridge import LiveBridge
from livebridge.components import SOURCE_MAP

class ControllerTests(asynctest.TestCase):

    def setUp(self):
        self.control_file = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        self.config_aws = {
            "access_key": "foo",
            "secret_key": "baz",
            "region":  "eu-central-1",
            "sqs_s3_queue": "http://foo-queue",
        }
        self.poll_interval = 10
        self.controller = Controller(config=self.config_aws, control_file=self.control_file, poll_interval=self.poll_interval)

        # set mock clients
        self.controller._sqs_client = MagicMock()

    @asynctest.ignore_loop
    def test_init(self):
        assert self.controller.config== self.config_aws
        assert self.controller.poll_interval == self.poll_interval
        assert self.controller.control_file == self.control_file
        assert isinstance(self.controller, Controller) == True 

    @asynctest.ignore_loop
    def test_sqs_client(self):
        assert self.controller._sqs_client == self.controller.sqs_client

    @asynctest.ignore_loop
    def test_run(self):
        self.controller.start_tasks = MagicMock()
        self.controller.read_control = True
        assert self.controller.control_data == None
        self.controller.run()
        assert self.controller.read_control == False
        assert type(self.controller.control_data) == dict
        self.controller.start_tasks.call_count == 1
        assert len(self.controller.tasked) == 0
  
    @asynctest.ignore_loop
    def test_run_failing(self):
        self.controller.start_tasks = MagicMock()
        self.controller.control_file = "/does/not/exist.yaml"
        assert len(self.controller.tasked) == 0
        assert self.controller.control_data == None
        self.controller.run()
        assert len(self.controller.tasked) == 1
        assert type(self.controller.tasked[0]) == asyncio.Task
        assert self.controller.start_tasks.called == 0
        assert self.controller.control_data == None

    @asynctest.ignore_loop
    def test_run_failing_reuse_existing_control(self):
        # run with existing control
        self.controller.start_tasks = MagicMock()
        self.controller.read_control = True
        assert self.controller.control_data == None
        self.controller.run()
        assert type(self.controller.control_data) == dict
        self.controller.start_tasks.call_count == 1

        # run again with failing control file
        existing_control = self.controller.control_data
        self.controller.control_file = "/does/not/exist.yaml"
        self.controller.run()
        assert len(self.controller.tasked) == 0
        assert self.controller.start_tasks.call_count == 2
        assert self.controller.control_data == existing_control

    async def test_run_retry(self):
        self.controller.run = asynctest.CoroutineMock()
        self.controller.retry_run_interval = 2
        assert self.controller.control_data == None
        await self.controller.retry_run()
        assert self.controller.run.called
        assert self.controller.run.call_count ==  1

    @asynctest.ignore_loop
    def test_start_tasks_with_watcher(self):
        c = ControlFile() 
        self.controller.control_data = c.load(self.control_file, resolve_auth=True)
        assert self.controller.bridges == {}
        assert self.controller.tasked == []
        self.controller.start_tasks()

        assert len(self.controller.bridges) == 2
        for bridge in self.controller.bridges:
            assert type(bridge) == LiveBridge

        assert len(self.controller.tasked) == 3
        for task in self.controller.tasked:
            assert type(task) == asyncio.tasks.Task
 
    @asynctest.ignore_loop
    def test_start_tasks_without_watcher(self):
        c = ControlFile() 
        self.controller.control_data = c.load(self.control_file, resolve_auth=True)
        del self.controller.config["sqs_s3_queue"]
        self.controller.start_tasks()

        assert len(self.controller.tasked) == 2
        for task in self.controller.tasked:
            assert type(task) == asyncio.tasks.Task
 
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

    async def test_run_poller(self):
        # mock coroutine, will set reread flag when called
        async def mock_routine():
            self.controller.read_control = True

        # mock bridge
        bridge1 = MagicMock()
        bridge1.check_posts = mock_routine

        self.controller.run = asynctest.CoroutineMock()
        self.controller.bridges = {bridge1: bridge1}

        # run and stop bridge1 
        assert self.controller.read_control == False
        await self.controller.run_poller(bridge=bridge1, interval=2)
        assert self.controller.read_control == True
        assert self.controller.run.call_count == 1
        
    async def test_run_poller_stopped(self):
        # make some mock bridges
        bridge1 = MagicMock()
        bridge2 = MagicMock()
        bridge1.check_posts = asynctest.CoroutineMock()
        self.controller.bridges = {bridge1: bridge1, bridge2: bridge2}
        self.controller.run = asynctest.CoroutineMock()
        self.controller.read_control = True        

        # stop bridge1 
        await self.controller.run_poller(bridge=bridge1)
        assert self.controller.run.call_count == 0
        assert self.controller.bridges.get(bridge1) == None
        assert self.controller.bridges.get(bridge2) == bridge2
        
        # stop bridge2 
        await self.controller.run_poller(bridge=bridge2)
        assert len(self.controller.bridges) == 0
        assert self.controller.run.call_count == 1

    async def test_run_streaming(self):
        # mock coroutine, will set reread flag when called
        async def stop():
            await asyncio.sleep(2)
            self.controller.read_control = True

        async def mock_routine():
            asyncio.Task(stop())

        bridge = MagicMock()
        bridge.listen_ws = asynctest.CoroutineMock(side_effect=mock_routine)
        bridge.source = MagicMock()
        bridge.source.stop = asynctest.CoroutineMock()
        self.controller.remove_bridge = asynctest.CoroutineMock()
        self.controller.read_control = False
        self.controller.shutdown = False
        await self.controller.run_stream(bridge=bridge)
        assert self.controller.remove_bridge.call_count == 1
        assert bridge.source.stop.call_count == 1

    @asynctest.ignore_loop
    def test_append_streaming_bridge(self):
        class Source:
            mode = "streaming"
            def __init__(self, **kwargs): 
                pass
        SOURCE_MAP["liveblog"] = Source
        assert len(self.controller.bridges) == 0
        config = {"mode": "streaming", "type": "liveblog", "targets": [{"type": "scribble"}]}
        self.controller.append_bridge(config)
        assert len(self.controller.bridges) == 1
        for bridge in self.controller.bridges.keys():
            assert self.controller.bridges[bridge].__name__ == "run_stream"

    @asynctest.ignore_loop
    def test_append_poller_bridge(self):
        class Source:
            mode = "polling"
            def __init__(self, **kwargs): 
                pass
        SOURCE_MAP["liveblog"] = Source
        assert len(self.controller.bridges) == 0
        config = {"mode": "polling", "type": "liveblog", "targets": [{"type": "scribble"}]}
        self.controller.append_bridge(config)
        assert len(self.controller.bridges) == 1
        for bridge in self.controller.bridges.keys():
            assert self.controller.bridges[bridge].__name__ == "run_poller"

    @asynctest.ignore_loop
    def test_remove_bridge(self):
        bridge1 = MagicMock()
        bridge2 = MagicMock()
        self.controller.bridges = {bridge1: "foo", bridge2: "baz"}
        self.controller.run = asynctest.CoroutineMock()
        self.controller.read_control = True

        # remove bridge 1
        self.controller.remove_bridge(bridge1)
        assert len(self.controller.bridges) == 1
        assert bridge2 in self.controller.bridges.keys()
        assert self.controller.run.called == 0

        # remove bridge 2
        self.controller.remove_bridge(bridge2)
        assert len(self.controller.bridges) == 0
        assert self.controller.run.called == 1