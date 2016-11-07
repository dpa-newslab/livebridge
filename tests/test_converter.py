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
import os.path
from livebridge.components import get_converter, add_converter
from livebridge.base import BaseConverter


class TestConverter(BaseConverter):
    source = "foo"
    target = "baz"


class ConverterTest(asynctest.TestCase):

    async def setUp(self):
        self.converter = TestConverter()
        add_converter(TestConverter)

    @asynctest.ignore_loop
    def test_get_converter(self):
        converter = get_converter("foo", "baz")
        assert type(converter) == TestConverter
        assert converter.source == "foo"
        assert converter.target == "baz"

        assert None == get_converter("foo", "foobaz")

    async def test_not_implemented(self):
        converter = TestConverter()
        try:
            c = await converter.convert({})
        except Exception as e:
            assert type(e) == NotImplementedError

    async def test_download_image(self):
        pic_data = {
            "href": "http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/7966946203766696aed8d067b04972b3a8f695aac885b51675d4117b388c1454",
            "media": "7966946203766696aed8d067b04972b3a8f695aac885b51675d4117b388c1454",
            "mimetype": "image/jpeg",
        }
        filepath = await self.converter._download_image(pic_data)
        assert filepath.startswith("/tmp/") == True
        assert filepath.endswith("-{}.jpeg".format(pic_data["media"])) == True
        assert os.path.exists(filepath) == True
        await self.converter.remove_images([filepath])
        assert os.path.exists(filepath) == False

    async def test_remove_invalid_images(self):
        res = await self.converter.remove_images(["/non/path/file"])
        assert res == None
