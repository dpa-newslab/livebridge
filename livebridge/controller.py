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
import aiobotocore
import asyncio
import logging
import json
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
                                    region_name = self.config["region"],
                                    aws_secret_access_key = self.config["secret_key"] or None,
                                    aws_access_key_id = self.config["access_key"] or None)
        return self._sqs_client

    async def clean_shutdown(self):
        logger.info("Requesting proper shutdown of tasks.")
        self.shutdown = True
        while len(self.bridges) > 0:
            await asyncio.sleep(1)
        return True

    async def check_control_change(self):
        client = self.sqs_client
        logger.info("Starting watching for control file changes on s3.")
        try:
            # purge queue before starting watching
            purge_resp = await client.purge_queue(
                QueueUrl=self.config["sqs_s3_queue"]
            )
            logger.info("Purged SQS queue {}".format(self.config["sqs_s3_queue"]))
        except ClientError as e:
            logger.warning("Purging SQS queue failed with: {}".format(e))
        # check for update events
        while True:
            try:
                response = await client.receive_message(
                    QueueUrl=self.config["sqs_s3_queue"]
                )
                for msg in response.get("Messages", []):
                    logger.debug("SQS {}".format(msg.get("MessageId")))
                    body = msg.get("Body")
                    data = json.loads(body) if body else None
                    del_res = await client.delete_message(
                        QueueUrl=self.config["sqs_s3_queue"],
                        ReceiptHandle=msg.get("ReceiptHandle")
                    )
                    if data:
                        for rec in data.get("Records", []):
                            self.read_control = True
                            logger.debug("EVENT: {} {}".format(rec.get("s3", {}).get("object", {}).get("key"), rec.get("eventName")))
                            return
            except Exception as e:
                logger.error("Error fetching SQS messages with: {}".format(e))
            await asyncio.sleep(60)

    def append_bridge(self, config_data):
        bridge = LiveBridge(config_data)
        for t in config_data.get("targets", []):
            target_client = get_target(t)
            bridge.add_target(target_client)
        # start specific source 
        if bridge.source.mode == "streaming":
            self.bridges[bridge] = self.run_stream(bridge=bridge)
        elif bridge.source.mode == "polling":
            self.bridges[bridge] = self.run_poller(bridge=bridge, interval=self.poll_interval)

    def remove_bridge(self, bridge):
        logger.info("ENDING: {}".format(bridge))
        task = self.bridges[bridge]
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
            c = ControlFile()
            control_data = c.load(self.control_file, resolve_auth=True)
        except Exception as e:
            logger.error("Error when reading control file.")
            logger.error(e)
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
        # start content bridges
        for b in self.control_data["bridges"]:
            self.append_bridge(b)

        # create futures for bridges
        for b in self.bridges:
            self.tasked.append(asyncio.Task(self.bridges[b]))

        # listen to s3 control changes if sqs queue is given
        if self.config.get("sqs_s3_queue"):
            self.tasked.append(asyncio.Task(self.check_control_change()))

    async def run_stream(self, *, bridge):
        future = await bridge.listen_ws()
        while True and self.read_control != True and self.shutdown != True:
            # wait for shutdown
            await asyncio.sleep(4)
        await bridge.source.stop()

        self.remove_bridge(bridge)
        return 

    async def run_poller(self, *, bridge, interval=180):
        # initialize liveblogs to watch
        while True and self.read_control != True and self.shutdown != True:
            #logger.debug("Checked new posts for {} on {}".format(bridge.source_id, bridge.endpoint))
            await bridge.check_posts()
            # wait
            await asyncio.sleep(interval)

        self.remove_bridge(bridge)
        return 
