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
import pytest
import asynctest 
from livebridge.storages.base import BaseStorage

class PostTest(asynctest.TestCase):

    def setUp(self):
        self.storage = BaseStorage()

    async def test_parent_methods(self):
        with self.assertRaises(NotImplementedError):
            await self.storage.db

        with self.assertRaises(NotImplementedError):
            self.storage.setup()

        with self.assertRaises(NotImplementedError):
            await self.storage.insert_post(**{})

        with self.assertRaises(NotImplementedError):
            await self.storage.get_last_updated(source_id="foo")

        with self.assertRaises(NotImplementedError):
            await self.storage.get_post(target_id="one", post_id="two")

        with self.assertRaises(NotImplementedError):
            await self.storage.update_post(target_id="one", post_id="two")

        with self.assertRaises(NotImplementedError):
            await self.storage.delete_post(target_id="one", post_id="two")