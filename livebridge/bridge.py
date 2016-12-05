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
from livebridge.components import get_converter, get_post, get_source, get_db_client


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
        self.queue = asyncio.Queue()
        self.queue_task = asyncio.ensure_future(self._queue_consumer())
        self.sleep_tasks = []

    def __repr__(self):
        return "<LiveBridge [{}] {} {}>".format(self.label, self.endpoint, self.source_id)

    @property
    def source(self):
        if self.api_client:
            return self.api_client
        # setup api client
        self.api_client = get_source(self.config)
        return self.api_client

    def stop(self):
        self.queue_task.cancel()
        for t in self.sleep_tasks:
            t.cancel()
        return True

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
                asyncio.ensure_future(self.new_posts(posts))
        except Exception as e:
            logger.error("Fatal checking {}{}".format(getattr(self, "endpoint", "-"), self.source_id))
            logger.exception(e)
        return True

    async def _sleep(self, seconds):
        try:
            task = asyncio.ensure_future(asyncio.sleep(seconds))
            self.sleep_tasks.append(task)
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self.sleep_tasks.remove(task)
        return True

    async def _action_done(self, fn, item):
        exc = fn.exception()
        if exc:
            logger.error("TARGET ACTION FAILED, WILL RETRY: [{}] {} {} [{}]".format(
                         item["count"], item["post"], item["target"], exc))
            item["count"] = item["count"] + 1
            await self._sleep(5*item["count"])
            await self.queue.put(item)
        else:
            logger.info("POST {post.id} distributed to {target.target_id} [{count}]".format(**item))

    async def _process_action(self, task):
            t = asyncio.ensure_future(task["target"].handle_post(task["post"]))
            cb = lambda fn: asyncio.ensure_future(self._action_done(fn, task))
            t.add_done_callback(cb)

    async def _queue_consumer(self):
        try:
            while True:
                task = await self.queue.get()
                self.queue.task_done()
                if task["count"] > 10:
                    logger.debug("DISTRIBUTION ABORTED: {post.id} {target.target_id} [{count}]".format(**task))
                    continue
                asyncio.ensure_future(self._process_action(task))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("WORKER QUEUE FAILED: {}".format(e))
            logger.exception(e)
                                    
    async def new_posts(self, posts):
        try:
            logger.info("##### Received {} posts from {}".format(len(posts), self.source))
            for p in posts:
                for t in self.targets:
                    post = copy.deepcopy(p)
                    item ={"post":post, "target": t, "count": 0}
                    await self.queue.put(item)
                # update last updated property in source client
                self.source.last_updated = p.updated
        except Exception as e:
            logger.error("Handling new posts failed [{}]: {}".format(self.source, e))
