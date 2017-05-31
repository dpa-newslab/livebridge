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
import aiobotocore
import boto3
import json
import logging
import os
import yaml
from botocore.client import Config
from botocore.exceptions import ClientError
from livebridge.config import AWS
from livebridge.controldata.base import BaseControl

logger = logging.getLogger(__name__)

class ControlFile(BaseControl):

    def __init__(self):
        self._sqs_client = None
        self.config = AWS

    def __del__(self):
        if self._sqs_client:
            self._sqs_client.close()

    @property
    async def sqs_client(self):
        if self._sqs_client:
            return self._sqs_client
        session = aiobotocore.get_session()
        self._sqs_client = session.create_client('sqs',
             region_name=self.config["region"],
             aws_secret_access_key=self.config["secret_key"] or None,
             aws_access_key_id=self.config["access_key"] or None)

        await self._purge_sqs_queue()

        return self._sqs_client

    async def _purge_sqs_queue(self):
        # purge queue before starting watching
        try:
            await self._sqs_client.purge_queue(
                QueueUrl=self.config["sqs_s3_queue"]
            )
            logger.info("Purged SQS queue {}".format(self.config["sqs_s3_queue"]))
        except ClientError as exc:
            logger.warning("Purging SQS queue failed with: {}".format(exc))

    async def check_control_change(self):
        client = await self.sqs_client
        # check for update events
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
                        return True
        except Exception as exc:
            logger.error("Error fetching SQS messages with: {}".format(exc))
        return False

    async def load(self, path, *, resolve_auth=False):
        if not path.startswith("s3://"):
            body = self._load_from_file(path)
        else:
            body = self._load_from_s3(path)
        return yaml.load(body)

    def _load_from_file(self, path):
        logger.info("Loading control file from disk: {}".format(path))
        if not os.path.exists(path):
            raise IOError("Path for control file not found.")

        file = open(path, "r")
        body = file.read()
        file.close()

        return body

    def _load_from_s3(self, url):
        bucket, key = url.split('/', 2)[-1].split('/', 1)
        logger.info("Loading control file from s3: {} - {}".format(bucket, key))
        config = Config(signature_version="s3v4") if self.config["region"] in ["eu-central-1"] else None
        client = boto3.client(
            's3',
            region_name=self.config["region"],
            aws_access_key_id=self.config["access_key"] or None,
            aws_secret_access_key=self.config["secret_key"] or None,
            config=config,
        )
        control_file = client.get_object(Bucket=bucket, Key=key)
        return control_file["Body"].read()
