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


class MockConverter(BaseConverter):
    source = "foo"
    target = "baz"


class ConverterTest(asynctest.TestCase):

    async def setUp(self):
        self.converter = MockConverter()
        add_converter(MockConverter)

    @asynctest.ignore_loop
    def test_get_converter(self):
        converter = get_converter("foo", "baz")
        assert type(converter) == MockConverter
        assert converter.source == "foo"
        assert converter.target == "baz"

        assert None == get_converter("foo", "foobaz")

    async def test_not_implemented(self):
        converter = MockConverter()
        try:
            c = await converter.convert({})
        except Exception as e:
            assert type(e) == NotImplementedError

    async def test_download_image_without_file_ext(self):
        pic_data = {
            "href": "http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/7966946203766696aed8d067b04972b3a8f695aac885b51675d4117b388c1454",
            "media": "7966946203766696aed8d067b04972b3a8f695aac885b51675d4117b388c1454",
            "mimetype": "image/jpeg",
        }
        filepath = await self.converter._download_image(pic_data)
        assert filepath.startswith("/tmp/") == True
        assert filepath.endswith("-{}.jpg".format(os.path.basename(pic_data["media"]))) == True
        assert os.path.exists(filepath) == True
        await self.converter.remove_images([filepath])
        assert os.path.exists(filepath) == False

    async def test_download_image_with_file_ext(self):
        pic_data = {
            "href": "https://dpa.liveblog.pro/dpa/2017013113018/47ac1bb4827ac9c8e214d3d35c202696be4569bd8d5324fd4db1548b3edf81e8.jpg",
            "media": "dpa/2017013113018/b5f35ff838f87cfe73961dec8f4db10d42e1db816933b1d1816afb48ed96fb59.jpg",
            "mimetype": "image/jpeg",
        }
        filepath = await self.converter._download_image(pic_data)
        assert filepath.startswith("/tmp/") == True
        assert filepath.endswith(".jpg.jpg") == False
        assert filepath.endswith("-{}".format(os.path.basename(pic_data["media"]))) == True
        assert os.path.exists(filepath) == True
        await self.converter.remove_images([filepath])
        assert os.path.exists(filepath) == False

    async def test_remove_invalid_images(self):
        res = await self.converter.remove_images(["/non/path/file"])
        assert res == None
