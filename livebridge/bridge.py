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
import asyncio
import copy
import logging
from livebridge.config import RETRY_MULTIPLIER, MAX_RETRIES
from livebridge.components import get_source, get_db_client, get_hash
from livebridge.base import InvalidTargetResource

logger = logging.getLogger(__name__)


class LiveBridge(object):

    def __init__(self, config):
        self.targets = []
        self.api_client = None
        self.config = config
        self.hash = get_hash(self.config)
        self.source_id = self.config.get("source_id")
        self.endpoint = self.config.get("endpoint")
        self.label = self.config.get("label", "-")
        self.retry_multiplier = RETRY_MULTIPLIER
        self.max_retries = MAX_RETRIES
        self.db = get_db_client()
        self.queue = asyncio.Queue()
        self.queue_task = None
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
        # stop queue task first
        if self.queue_task:
            self.queue_task.cancel()
        # stop sleeping tasks
        for task in self.sleep_tasks:
            task.cancel()
        return True

    def add_target(self, target):
        logger.debug("Adding target {} to {}".format(target, self))
        self.targets.append(target)

    async def listen_ws(self):
        return asyncio.Task(self.source.listen(self.new_posts))

    async def check_posts(self):
        try:
            posts = await self.source.poll()
            if posts:
                await self.new_posts(posts)
        except Exception as exc:
            logger.error("Fatal checking {}{}".format(getattr(self, "endpoint", "-"), self.source_id))
            logger.exception(exc)
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

    async def _action_done(self, future, item):
        # set task as done
        self.queue.task_done()

        # handle action result
        exc = future.exception()
        if exc and type(exc) is InvalidTargetResource:
            logger.warning("POST {post.id} not distributed to {target.target_id} [{count}], no retry.".format(**item))
            logger.warning(exc)
        elif exc:
            logger.error("TARGET ACTION FAILED, WILL RETRY: [{}] {} {} [{}]".format(
                item["count"], item["post"], item["target"], exc))
            if item["count"] >= self.max_retries:
                logger.info("DISTRIBUTION ABORTED: {post.id} {target.target_id} [{count}]".format(**item))
            else:
                item["count"] = item["count"] + 1
                await self._sleep(self.retry_multiplier * item["count"])
                await self._put_to_queue(item)
        else:
            logger.info("POST {post.id} distributed to {target.target_id} [{count}]".format(**item))

    async def _put_to_queue(self, item):
        if not self.queue_task:
            self.queue_task = asyncio.ensure_future(self._queue_consumer())
        await self.queue.put(item)

    async def _process_action(self, task):
        fut = asyncio.ensure_future(task["target"].handle_post(task["post"]))
        callback = lambda fn: asyncio.ensure_future(self._action_done(fn, task))
        fut.add_done_callback(callback)

    async def _queue_consumer(self):
        try:
            while True:
                task = await self.queue.get()
                asyncio.ensure_future(self._process_action(task))
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("WORKER QUEUE FAILED: {}".format(exc))
            logger.exception(exc)

    async def new_posts(self, posts):
        try:
            logger.info("##### Received {} posts from {}".format(len(posts), self.source))
            for new_post in posts:
                for target in self.targets:
                    post = copy.deepcopy(new_post)
                    item = {"post": post, "target": target, "count": 0}
                    await self._put_to_queue(item)
                # wait until post is processed
                await self.queue.join()
        except Exception as exc:
            logger.error("Handling new posts failed [{}]: {}".format(self.source, exc))
