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
from livebridge.base import PollingSource, StreamingSource
from livebridge.components import get_source, add_source

class TestSource(StreamingSource):
    type = "test"
    def __init__(self, *, config={}, **kwargs):
        self.foo = config.get("foo")

class BaseSourcesTest(asynctest.TestCase):

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
