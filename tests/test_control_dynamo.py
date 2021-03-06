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
from livebridge.storages import DynamoClient
from livebridge.controldata.dynamo import DynamoControl


class DynamoControlTest(asynctest.TestCase):

    def setUp(self):
        self.control = DynamoControl()

    async def test_dynamo_client(self):
        client = await self.control.db_client
        assert self.control._db_client == client

    async def test_new_db_client(self):
        assert self.control._db_client is None
        client = await self.control.db_client
        assert type(client) == DynamoClient
        assert self.control._db_client == client

        client = await self.control.db_client
        assert self.control._db_client == client

    async def test_check_control_change(self):
        data = {"auth": {}, "bridges": []}
        self.control._load_control_data = asynctest.CoroutineMock(return_value=data)
        self.control._checksum = "no-foobaz"
        self.control._get_checksum = asynctest.CoroutineMock(return_value="foobaz")
        res = await self.control.check_control_change()
        assert res is True
        assert self.control._load_control_data.call_count == 1
        self.control._get_checksum.called_once_with(data)

    async def test_check_control_change_with_exception(self):
        self.control._load_control_data = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.control.check_control_change()
        assert res is False
        assert self.control._load_control_data.call_count == 1

    async def test_load(self):
        data = {"auth": {}, "bridges": []}
        self.control._load_control_data = asynctest.CoroutineMock(return_value=data)
        res = await self.control.load("path")
        assert res == data
        assert len(self.control._checksum) == 32

    async def test_load_control_data(self):
        data = {"auth": {}, "bridges": []}
        self.control._db_client = asynctest.MagicMock()
        self.control._db_client.get_control = asynctest.CoroutineMock(return_value=data)
        res = await self.control._load_control_data()
        assert res == data

    async def test_save(self):
        self.control._db_client = asynctest.MagicMock(spec=DynamoClient)
        self.control._db_client.save_control.return_value = True
        path = "/tmp/lb_dynamo_test_save.txt"
        data = {"foo": "bla"}
        res = await self.control.save(path, data)
        assert res is True
        assert self.control._db_client.save_control.call_count == 1
        assert self.control._db_client.save_control.call_args[0][0] == data
