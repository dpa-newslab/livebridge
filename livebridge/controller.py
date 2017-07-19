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
import logging
from livebridge.components import get_target
from livebridge.bridge import LiveBridge
from livebridge.controldata import ControlData

logger = logging.getLogger(__name__)

class Controller(object):

    def __init__(self, config, control_file):
        self.config = config
        self.control_file = control_file
        self.poll_interval = config.POLL_INTERVAL or 60
        self.check_control_interval = config.POLL_CONTROL_INTERVAL or 60
        self.read_control = False
        self.tasked = []
        self.sleep_tasks = []
        self.bridges = {}
        self.retry_run_interval = 30
        self.control_data = None # access to data from control file
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
        logger.info("Starting watching for control data changes.")
        while True and self.shutdown != True:
            is_changed = await self.control_data.check_control_change(self.control_file)
            if is_changed == True:
                if self.bridges:
                    # running bridges
                    self.read_control = True
                    await self.stop_bridges()
                else:
                    logger.info("No running bridges found, start with new control data.")
                    asyncio.ensure_future(self.run())
                return True
            await self.sleep(self.check_control_interval)

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

    def remove_bridge(self, bridge):
        logger.info("ENDING: {}".format(bridge))
        del self.bridges[bridge]
        if self.read_control and not self.bridges:
            logger.info("RESTART BRIDGES")
            asyncio.ensure_future(self.run())

    async def save_control_data(self, doc):
        control_data = ControlData(config=self.config)
        return await control_data.save(self.control_file, doc)

    async def load_control_data(self, resolve_auth=True):
        control_data = ControlData(config=self.config)
        await control_data.load(self.control_file, resolve_auth=resolve_auth)
        return control_data

    async def retry_run(self):
        logger.info("Will retry loading control file in 30 seconds.")
        await asyncio.sleep(self.retry_run_interval)
        asyncio.ensure_future(self.run())

    async def run(self):
        self.read_control = False
        loaded = False
        control_data = None
        try:
            control_data = await self.load_control_data()
            loaded = True
        except Exception as exc:
            logger.error("Error when reading control file.")
            logger.error(exc)
            logger.info("Will try to reuse existing control data.")

        # set new control data
        if loaded:
            logger.info("Using fetched control data.")
            self.control_data = control_data

        # (re)start tasks or retry fetching control file
        if self.control_data:
            self.start_tasks()
        else:
            self.tasked.append(asyncio.Task(self.retry_run()))

    def start_tasks(self):
        # append content bridges
        for bridge_config in self.control_data.list_bridges():
            self.append_bridge(bridge_config)

        # create futures for bridges
        for bridge in self.bridges:
            self.tasked.append(asyncio.Task(self.bridges[bridge]))

        # listen to s3 control changes
        self.tasked.append(asyncio.Task(self.check_control_change()))

    async def run_stream(self, *, bridge):
        await bridge.listen_ws()
        while True and self.read_control != True and self.shutdown != True:
            # wait for shutdown
            await self.sleep(4)

        # stop bridge
        try:
            await bridge.source.stop()
        except Exception as exc:
            logger.error("Error when stopping stream: {}".format(exc))

        self.remove_bridge(bridge)

    async def sleep(self, seconds):
        if self.read_control is True or self.shutdown is True:
            # if shutdown or restart is requested, don't fall asleep again
            return True

        try:
            task = asyncio.ensure_future(asyncio.sleep(seconds))
            self.sleep_tasks.append(task)
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self.sleep_tasks.remove(task)
        return True

    async def run_poller(self, *, bridge, interval=180):
        # initialize liveblogs to watch
        while True and self.read_control != True and self.shutdown != True:
            #logger.debug("Checked new posts for {} on {}".format(bridge.source_id, bridge.endpoint))
            await bridge.check_posts()
            await self.sleep(interval)

        self.remove_bridge(bridge)
        return
