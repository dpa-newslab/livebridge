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
import logging
from livebridge.components import get_target, get_hash
from livebridge.bridge import LiveBridge
from livebridge.controldata import ControlData

logger = logging.getLogger(__name__)


class Controller(object):

    def __init__(self, config, control_file):
        self.config = config
        self.control_file = control_file
        self.poll_interval = config.POLL_INTERVAL or 60
        self.check_control_interval = config.POLL_CONTROL_INTERVAL or 60
        self.force_check_control_data = config.CONTROLFILE_WATCH
        self.tasked = []
        self.sleep_tasks = []
        self.bridges = {}
        self.retry_run_interval = 30
        self.control_data = None  # access to data from control file
        self.shutdown = False

    async def clean_shutdown(self):
        logger.info("Requesting proper shutdown of tasks.")
        self.shutdown = True
        await self.stop_bridges()
        while len(self.bridges) > 0:
            logger.debug("Running bridges left: {}".format(len(self.bridges)))
            await asyncio.sleep(1)

    async def stop_bridges(self):
        """Stop all sleep tasks to allow bridges to end."""
        for task in self.sleep_tasks:
            task.cancel()
        for bridge in self.bridges:
            bridge.stop()

    async def check_control_change(self):
        # check for update events
        if self.control_data.is_auto_update() is False and \
            self.force_check_control_data != True:
            logger.info("Watching for control data changes deactivated.")
            return None

        logger.info("Starting watching for control data changes.")
        while True and self.shutdown is not True:
            is_changed = await self.control_data.check_control_change(self.control_file)
            if is_changed is True:
                asyncio.ensure_future(self.run())
                logger.info("Stopped watching for control data changes.")
                return True
            await self.sleep(self.check_control_interval)

    async def save_control_data(self, doc):
        control_data = ControlData(config=self.config)
        return await control_data.save(self.control_file, doc)

    async def load_control_data(self, resolve_auth=True):
        if not self.control_data:
            self.control_data = ControlData(config=self.config)
        await self.control_data.load(self.control_file, resolve_auth=resolve_auth)
        return self.control_data

    async def retry_run(self):
        logger.info("Will retry loading control file in 30 seconds.")
        await asyncio.sleep(self.retry_run_interval)
        asyncio.ensure_future(self.run())

    async def run(self):
        loaded = False
        try:
            await self.load_control_data()
            loaded = True
        except Exception as exc:
            logger.error("Error when reading control file.")
            logger.error(exc)
            logger.info("Will try to reuse existing control data.")

        # (re)start tasks or retry fetching control file
        if loaded and self.control_data:
            try:
                logger.info("Using fetched control data.")
                await self.remove_old_bridges()
                await self.add_new_bridges()
                # listen to control changes
                self.tasked.append(asyncio.Task(self.check_control_change()))
                return True
            except Exception as exp:
                logger.error("Error when adding/removing bridges")
                logger.exception(exp)

        # something went wrong, retry again
        self.tasked.append(asyncio.Task(self.retry_run()))
        return False

    async def add_new_bridges(self):
        # append content bridges
        for bridge_config in self.control_data.list_new_bridges():
            bridge = self.append_bridge(bridge_config)
            self.tasked.append(asyncio.Task(self.bridges[bridge]))

    async def remove_old_bridges(self):
        # identify removed bridges
        removed = [get_hash(c) for c in self.control_data.list_removed_bridges()]
        to_stop = [bridge for bridge in self.bridges if bridge.hash in removed]
        # stop removed bridges
        for bridge in to_stop:
            self.bridges[bridge].close()
            await self.remove_bridge(bridge)
            bridge.stop()

    def append_bridge(self, config_data):
        bridge = LiveBridge(config_data)
        for tconf in config_data.get("targets", []):
            target_client = get_target(tconf)
            bridge.add_target(target_client)
        # start specific source
        if bridge.source.mode == "streaming":
            self.bridges[bridge] = self.run_stream(bridge=bridge)
        elif bridge.source.mode == "polling":
            # custom source polling intervall set in control file?
            poll_interval = config_data["poll_interval"] if config_data.get("poll_interval") else self.poll_interval
            self.bridges[bridge] = self.run_poller(bridge=bridge, interval=poll_interval)
        return bridge

    async def remove_bridge(self, bridge):
        try:
            # special treatment for bridges with stop method
            if hasattr(bridge.source, "stop"):
                await bridge.source.stop()
        except Exception as exc:
            logger.error("Error when stopping stream: {}".format(exc))
            logger.exception(exc)

        logger.info("ENDING: {}".format(bridge))
        del self.bridges[bridge]

    async def run_stream(self, *, bridge):
        await bridge.listen_ws()

        while True and self.shutdown is not True:
            # wait for shutdown
            await self.sleep(4)

        await self.remove_bridge(bridge)

    async def run_poller(self, *, bridge, interval=180):
        # initialize liveblogs to watch
        while True and self.shutdown is not True:
            # logger.debug("Checked new posts for {} on {}".format(bridge.source_id, bridge.endpoint))
            await bridge.check_posts()
            await self.sleep(interval)

        await self.remove_bridge(bridge)

    async def sleep(self, seconds):
        if self.shutdown is True:
            # if shutdown is requested, don't fall asleep again
            return False

        try:
            task = asyncio.ensure_future(asyncio.sleep(seconds))
            self.sleep_tasks.append(task)
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self.sleep_tasks.remove(task)
        return True
