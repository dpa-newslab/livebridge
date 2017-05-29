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
import asyncio
import asynctest
import unittest.mock
import os.path
from livebridge import LiveBridge

class RunTests(asynctest.TestCase):

    async def test_run_with_loop(self):
        self.loop.run_until_complete = asynctest.CoroutineMock(return_value=True)
        control_file = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        db_connector = asynctest.MagicMock()
        db_connector.setup = asynctest.CoroutineMock(return_value=True)
        with asynctest.patch("livebridge.components.get_db_client") as mocked_db_client:
            mocked_db_client.return_value = db_connector
            with asynctest.patch("livebridge.controller.Controller") as mocked_controller:
                mocked_controller.run = asynctest.CoroutineMock(return_value=True)
                with asynctest.patch("asyncio.ensure_future") as mocked_ensure:
                    mocked_ensure.return_value = True
                    from livebridge.run import main
                    livebridge = main(loop=self.loop, control=control_file)
                    assert type(livebridge) is LiveBridge

    async def test_run_with_args(self):
        with unittest.mock.patch("argparse.ArgumentParser.parse_args") as patched:
            patched.side_effect = [Exception()]
            with self.assertRaises(Exception):
                from livebridge.run import main
                livebridge = main(loop=self.loop)

    async def test_run(self):
        self.loop.run_forever = asynctest.CoroutineMock(return_value=True)
        self.loop.run_until_complete = asynctest.CoroutineMock(return_value=True)
        self.loop.close = asynctest.CoroutineMock(return_value=True)
        control_file = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        db_connector = asynctest.MagicMock()
        db_connector.setup = asynctest.CoroutineMock(return_value=True)
        with asynctest.patch("livebridge.config.CONTROLFILE") as mocked_config:
            mocked_config.return_value = control_file
            with asynctest.patch("livebridge.components.get_db_client") as mocked_db_client:
                mocked_db_client.return_value = db_connector
                with asynctest.patch("livebridge.controller.Controller") as mocked_controller:
                    mocked_controller.run = asynctest.CoroutineMock(return_value=True)
                    with asynctest.patch("asyncio.get_event_loop") as patched:
                        patched.return_value = self.loop
                        with asynctest.patch("asyncio.ensure_future") as mocked_ensure:
                            mocked_ensure.return_value = True
                            with asynctest.patch("livebridge.LiveBridge.finish") as patched2:
                                from livebridge.run import main
                                main()
                                assert self.loop.run_forever.call_count == 1
                                assert self.loop.close.call_count == 1
