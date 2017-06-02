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
import asynctest
from datetime import datetime
from livebridge.config import DB
from livebridge.storages import SQLStorage
from livebridge.controldata.sql import SQLControl


class SQLControlTest(asynctest.TestCase):

    def setUp(self):
        DB["dsn"] = "sqlite://"
        self.control = SQLControl()

    def tearDown(self):
        del DB["dsn"]

    async def test_dynamo_client(self):
        client = await self.control.db_client
        assert self.control._db_client == client

    async def test_new_db_client(self):
        db_connector = asynctest.MagicMock()
        db_connector.setup = asynctest.CoroutineMock(return_value=True)
        with asynctest.patch("livebridge.components.get_db_client") as mocked_db_client:
            mocked_db_client.return_value = db_connector
            assert self.control._db_client == None
            client = await self.control.db_client
            assert type(client) == SQLStorage
            assert self.control._db_client == client

            client = await self.control.db_client
            assert self.control._db_client == client

    async def test_check_control_change(self):
        self.control._updated = datetime.now()
        data = {"auth": {}, "bridges": []}
        self.control._load_control_data = asynctest.CoroutineMock(return_value=data)
        res = await self.control.check_control_change()
        assert res == True
        assert self.control._load_control_data.call_count == 1

    async def test_check_control_change_initial(self):
        self.control._load_control_data = asynctest.CoroutineMock(return_value={})
        res = await self.control.check_control_change()
        assert res == False
        assert self.control._load_control_data.call_count == 0

    async def test_check_control_change_with_exception(self):
        self.control._updated = datetime.now()
        self.control._load_control_data = asynctest.CoroutineMock(side_effect=Exception())
        res = await self.control.check_control_change()
        assert res == False
        assert self.control._load_control_data.call_count == 1

    async def test_load(self):
        data = {"data": {"auth": {}, "bridges": []}, "updated": datetime.now()}
        self.control._load_control_data = asynctest.CoroutineMock(return_value=data)
        res = await self.control.load("path")
        assert res == data["data"]
        assert self.control._load_control_data.call_count == 1

    async def test_load_control_data(self):
        data = {"auth": {}, "bridges": []}
        self.control._updated = datetime.now()
        self.control._db_client = asynctest.MagicMock()
        self.control._db_client.get_control = asynctest.CoroutineMock(return_value=data)
        res = await self.control._load_control_data()
        assert res == data
