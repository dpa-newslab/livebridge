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
import asynctest
from livebridge import LiveBridge


class LoaderTests(asynctest.TestCase):

    def setUp(self):
        self.controller = asynctest.MagicMock()
        self.lb = LiveBridge(loop=self.loop, controller=self.controller)

    @asynctest.fail_on(unused_loop=False)
    def test_init(self):
        assert self.lb.controller == self.controller
        assert self.lb.loop == self.loop

    async def test_finish(self):
        tasks = [
            asynctest.MagicMock(cancel=asynctest.CoroutineMock(), exception=asynctest.MagicMock(return_value=False)),
            asynctest.MagicMock(cancel=asynctest.CoroutineMock(), done=lambda: False),
            asynctest.MagicMock(cancel=asynctest.CoroutineMock())
        ]
        await self.lb.finish(tasks)
        assert tasks[0].cancel.call_count == 1
        assert tasks[0].done.call_count == 1
        assert tasks[0].set_exception.call_count == 0
        assert tasks[1].cancel.call_count == 0
        assert tasks[1].set_exception.call_count == 1
        assert tasks[2].cancel.call_count == 0
        assert tasks[2].done.call_count == 1
        assert tasks[0].set_exception.call_count == 0

    @asynctest.fail_on(unused_loop=False)
    def test_shutdown(self):
        self.lb.controller.clean_shutdown = asynctest.CoroutineMock(return_value=True)
        self.lb.controller.tasked = [1, 2]
        self.lb.finish = asynctest.CoroutineMock(return_value=True)
        self.loop._default_executor = asynctest.MagicMock(shutdown=asynctest.CoroutineMock(return_value=True))

        self.lb.shutdown()
        assert self.lb.controller.clean_shutdown.call_count == 1
        assert self.lb.finish.call_count == 1
        assert self.lb.finish.call_args == asynctest.call([1, 2])
        assert self.loop._default_executor.shutdown.call_count == 1
