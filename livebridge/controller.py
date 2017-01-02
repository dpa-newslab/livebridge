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
import json
import aiobotocore
from botocore.exceptions import ClientError
from livebridge.components import get_target
from livebridge.bridge import LiveBridge
from livebridge.controlfile import ControlFile

logger = logging.getLogger(__name__)

class Controller(object):

    def __init__(self, config, control_file, poll_interval=60):
        self.config = config
        self.control_file = control_file
        self.poll_interval = poll_interval
        self.read_control = False
        self.tasked = []
        self.sleep_tasks = []
        self.bridges = {}
        self._sqs_client = None
        self.retry_run_interval = 30
        self.control_data = None # data from control file
        self.shutdown = False

    def __del__(self):
        if self._sqs_client:
            self._sqs_client.close()

    @property
    def sqs_client(self):
        if self._sqs_client:
            return self._sqs_client
        loop = asyncio.get_event_loop()
        session = aiobotocore.get_session(loop=loop)
        self._sqs_client = session.create_client('sqs',
                                                 region_name=self.config["region"],
                                                 aws_secret_access_key=self.config["secret_key"] or None,
                                                 aws_access_key_id=self.config["access_key"] or None)
        return self._sqs_client

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
        client = self.sqs_client
        logger.info("Starting watching for control file changes on s3.")
        try:
            # purge queue before starting watching
            await client.purge_queue(
                QueueUrl=self.config["sqs_s3_queue"]
            )
            logger.info("Purged SQS queue {}".format(self.config["sqs_s3_queue"]))
        except ClientError as exc:
            logger.warning("Purging SQS queue failed with: {}".format(exc))
        # check for update events
        while True and self.shutdown != True:
            try:
                response = await client.receive_message(
                    QueueUrl=self.config["sqs_s3_queue"]
                )
                for msg in response.get("Messages", []):
                    logger.debug("SQS {}".format(msg.get("MessageId")))
                    body = msg.get("Body")
                    data = json.loads(body) if body else None
                    await client.delete_message(
                        QueueUrl=self.config["sqs_s3_queue"],
                        ReceiptHandle=msg.get("ReceiptHandle")
                    )
                    if data:
                        for rec in data.get("Records", []):
                            logger.debug("EVENT: {} {}".format(
                                rec.get("s3", {}).get("object", {}).get("key"), rec.get("eventName")))
                            self.read_control = True
                            await self.stop_bridges()
                            return
            except Exception as exc:
                logger.error("Error fetching SQS messages with: {}".format(exc))
            await self.sleep(60)
        client.close()

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
            self.run()

    async def retry_run(self):
        logger.info("Will retry loading control file in 30 seconds.")
        await asyncio.sleep(self.retry_run_interval)
        self.run()

    def run(self):
        """ Blocking code."""
        self.read_control = False
        control_data = None
        try:
            cfile = ControlFile()
            control_data = cfile.load(self.control_file, resolve_auth=True)
        except Exception as exc:
            logger.error("Error when reading control file.")
            logger.error(exc)
            logger.info("Will try to reuse existing control data.")

        # set new control data
        if control_data:
            logger.info("Using fetched control data.")
            self.control_data = control_data

        # (re)start tasks or retry fetching control file
        if self.control_data:
            self.start_tasks()
        else:
            self.tasked.append(asyncio.Task(self.retry_run()))

    def start_tasks(self):
        # append content bridges
        for bridge_config in self.control_data["bridges"]:
            self.append_bridge(bridge_config)

        # create futures for bridges
        for bridge in self.bridges:
            self.tasked.append(asyncio.Task(self.bridges[bridge]))

        # listen to s3 control changes if sqs queue is given
        if self.config.get("sqs_s3_queue"):
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
