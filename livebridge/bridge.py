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
import asyncio
import copy
import logging
from livebridge.storages import get_db_client
from livebridge.components import get_converter, get_post, get_source


logger = logging.getLogger(__name__)


class LiveBridge(object):

    def __init__(self, config):
        self.targets = []
        self.api_client = None
        self.config = config
        self.source_id = self.config.get("source_id")
        self.endpoint = self.config.get("endpoint")
        self.label = self.config.get("label", "-")
        self.db = get_db_client()

    def __repr__(self):
        return "<LiveBridge [{}] {} {}>".format(self.label, self.endpoint, self.source_id)

    @property
    def source(self):
        if self.api_client:
            return self.api_client
        # setup api client
        self.api_client = get_source(self.config)
        return self.api_client

    def add_target(self, target):
        logger.debug("Adding target {} to {}".format(target, self))
        self.targets.append(target)

    async def listen_ws(self):
        return asyncio.Task(self.source.listen(self.new_posts))

    async def check_posts(self):
        try:
            # set last_updated
            if not self.source.last_updated:
                self.source.last_updated = await self.db.get_last_updated(self.source_id)
                logger.info("LAST UPDATED: {} {}".format(self.source.last_updated, self.source))
            posts = await self.source.poll()
            if posts:
                await self.new_posts(posts)
        except Exception as e:
            logger.error("Fatal checking {}{}".format(getattr(self, "endpoint", "-"), self.source_id))
            logger.exception(e)
        return True

    async def _process_post(self, target, source_post):
        post = copy.deepcopy(source_post)
        # update last updated property in source client
        self.source.last_updated = post.updated
        # handle post in target
        await target.handle_post(post)

    async def new_posts(self, posts):
        logger.info("##### Received {} posts from {}".format(len(posts), self.source))
        for p in posts:
            coros = [self._process_post(t, p) for t in self.targets]
            await asyncio.gather(*coros)
        return True
