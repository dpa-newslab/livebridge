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
import logging
from livebridge.controldata.base import BaseControl
from livebridge.components import get_db_client, get_hash


logger = logging.getLogger(__name__)


class DynamoControl(BaseControl):

    def __init__(self):
        self._db_client = None
        self._checksum = None

    @property
    async def db_client(self):
        if self._db_client:
            return self._db_client
        self._db_client = get_db_client()
        return self._db_client

    async def _load_control_data(self):
        db_client = await self.db_client
        return await db_client.get_control()

    async def check_control_change(self, control_path=None):
        try:
            control_data = await self._load_control_data()
            if control_data and self._checksum and self._checksum != get_hash(control_data):
                return True
        except Exception as exc:
            logger.error("Error checking dynamo control data change with: {}".format(exc))
        return False

    async def load(self, path):
        control_data = await self._load_control_data()
        self._checksum = get_hash(control_data)
        return control_data

    async def save(self, path, data):
        db_client = await self.db_client
        return await db_client.save_control(data)
