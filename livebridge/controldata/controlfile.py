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
import json
import logging
import os
import os.path
import yaml
from botocore.exceptions import ClientError
from livebridge.config import AWS
from livebridge.controldata.base import BaseControl

logger = logging.getLogger(__name__)


class ControlFile(BaseControl):

    def __init__(self):
        self._sqs_client = None
        self._s3_client = None
        self.config = AWS
        self._updated_local = None
        self.auto_update = True

    def __del__(self):
        if self._sqs_client:
            self._sqs_client.close()

        if self._s3_client:
            self._s3_client.close()

    @property
    async def sqs_client(self):
        if self._sqs_client:
            return self._sqs_client
        session = aiobotocore.get_session()
        self._sqs_client = session.create_client(
            'sqs',
            region_name=self.config["region"],
            aws_secret_access_key=self.config["secret_key"] or None,
            aws_access_key_id=self.config["access_key"] or None)

        await self._purge_sqs_queue()

        return self._sqs_client

    @property
    def s3_client(self):
        if self._s3_client:
            return self._s3_client
        session = aiobotocore.get_session()
        self._s3_client = session.create_client(
            's3',
            region_name=self.config["region"],
            aws_secret_access_key=self.config["secret_key"] or None,
            aws_access_key_id=self.config["access_key"] or None)
        return self._s3_client

    async def _purge_sqs_queue(self):
        # purge queue before starting watching
        try:
            await self._sqs_client.purge_queue(
                QueueUrl=self.config["sqs_s3_queue"]
            )
            logger.info("Purged SQS queue {}".format(self.config["sqs_s3_queue"]))
        except ClientError as exc:
            logger.warning("Purging SQS queue failed with: {}".format(exc))

    async def check_control_change(self, control_path=None):
        if not self.config.get("sqs_s3_queue", False):
            return await self._check_local_changes(control_path)
        else:
            return await self._check_s3_changes()

    async def _check_local_changes(self, control_path):
        is_changed = False
        try:
            last_updated = os.stat(control_path).st_mtime
            if last_updated != self._updated_local:
                is_changed = True
            self._updated_local = last_updated
        except Exception as exc:
            logger.error("Error fetching last updated time of local control file: {}".format(exc))
        return is_changed

    async def _check_s3_changes(self):
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
            self.auto_update = False
            body = self._load_from_file(path)
        else:
            body = await self._load_from_s3(path)
        return yaml.load(body)

    def _load_from_file(self, path):
        logger.info("Loading control file from disk: {}".format(path))
        if not os.path.exists(path):
            raise IOError("Path for control file not found.")

        file = open(path, "r")
        body = file.read()
        self._updated_local = os.stat(path).st_mtime
        file.close()

        return body

    async def _save_to_file(self, path, data):
        logger.info("Saving control file to disk.")
        directory = os.path.dirname(os.path.abspath(path))
        if not os.access(directory, os.W_OK):
            raise IOError("Path for control file not writable: {}".format(path))

        file = open(path, "w+")
        file.write(data)
        file.close()

        return True

    async def _load_from_s3(self, url):
        bucket, key = url.split('/', 2)[-1].split('/', 1)
        logger.info("Loading control file from s3: {} - {}".format(bucket, key))
        control_file = await self.s3_client.get_object(Bucket=bucket, Key=key)
        control_data = await control_file["Body"].read()
        return control_data

    async def _save_to_s3(self, path, data):
        bucket, key = path.split('/', 2)[-1].split('/', 1)
        logger.info("Saving control file to s3: {} - {}".format(bucket, key))
        await self.s3_client.put_object(Body=data, Bucket=bucket, Key=key)
        return True

    async def save(self, path, data):
        res = False
        yaml_data = yaml.dump(data, indent=4, default_flow_style=False)
        if not path.startswith("s3://"):
            res = await self._save_to_file(path, yaml_data)
        else:
            res = await self._save_to_s3(path, yaml_data)
        return res
