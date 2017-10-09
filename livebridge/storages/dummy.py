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
from livebridge.storages.base import BaseStorage


logger = logging.getLogger(__name__)


class DummyStorage(BaseStorage):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DummyStorage, cls).__new__(cls)
            logger.debug("Dummy client: {}".format(cls._instance))
        return cls._instance

    def __init__(self, **kwargs):
        pass

    async def setup(self):
        return False

    async def get_last_updated(self, source_id):
        return None

    async def get_known_posts(self, source_id, post_ids):
        return []

    async def get_post(self, target_id, post_id):
        return None

    async def insert_post(self, **kwargs):
        return True

    async def update_post(self, **kwargs):
        return True

    async def delete_post(self, target_id, post_id):
        return True

    async def get_control(self, updated=None):
        return False
