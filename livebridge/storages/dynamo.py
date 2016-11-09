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
import aiobotocore
import logging
import json
from dateutil.parser import parse as parse_date
from datetime import datetime
from botocore.exceptions import BotoCoreError
from livebridge.storages.base import BaseStorage

logger = logging.getLogger(__name__)


class DynamoClient(BaseStorage):

    # date format for datetime values in DynamoDB
    date_fmt = "%Y-%m-%dT%H:%M:%S+00:00"

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DynamoClient, cls).__new__(cls)
            logger.debug("Dynamo client: {}".format(cls._instance))
        return cls._instance

    def __init__(self, **kwargs):
        self.access_key = kwargs.get("access_key") or None
        self.secret_key = kwargs.get("secret_key") or None
        self.region = kwargs.get("region")
        self.endpoint_url = kwargs.get("endpoint_url") or None
        self.table_name = kwargs.get("table_name")
        self.table_schema = {
            "TableName": self.table_name,
            "KeySchema": [
                { "AttributeName": "target_id", "KeyType": "HASH" },
                { "AttributeName": "post_id", "KeyType": "RANGE" }
            ],
            "AttributeDefinitions": [
                { "AttributeName": "updated", "AttributeType": "S" },
                { "AttributeName": "target_id", "AttributeType": "S" },
                { "AttributeName": "post_id", "AttributeType": "S" },
                { "AttributeName": "source_id", "AttributeType": "S" }
            ],
            "ProvisionedThroughput": { "ReadCapacityUnits": 3, "WriteCapacityUnits": 3 },
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "source_id-updated-index",
                    "KeySchema": [
                        { "AttributeName": "source_id", "KeyType": "HASH" },
                        { "AttributeName": "updated", "KeyType": "RANGE" }
                    ],
                    "Projection": { "ProjectionType": "KEYS_ONLY" },
                    "ProvisionedThroughput": { "ReadCapacityUnits": 2, "WriteCapacityUnits": 2 },
                }
            ]
        }

    def __del__(self):
        if hasattr(self, "db_client") and self.db_client:
            self.db_client.close()

    @property
    async def db(self):
        if hasattr(self, "db_client") and self.db_client:
            return self.db_client
        logger.info("DynamoDB: Connecting to region [{}] with endpoint_url [{}] and table [{}]".format(
                                self.region, self.endpoint_url or "-", self.table_name or "-"))
        loop = asyncio.get_event_loop()
        session = aiobotocore.get_session(loop=loop)
        self.db_client = session.create_client('dynamodb',
                                    region_name = self.region,
                                    endpoint_url = self.endpoint_url,
                                    aws_secret_access_key = self.secret_key,
                                    aws_access_key_id = self.access_key)
        # dirty fix for disabling crc32 checks
        self.db_client._endpoint._aio_session._default_headers["Accept-Encoding"] = ""
        return self.db_client

    async def setup(self):
        """Setting up DynamoDB table, if it not exists."""
        try:
            client = await self.db
            response = await client.list_tables()
            # create table if not already created.
            if self.table_name not in response["TableNames"]:
                logger.info("Creating DynamoDB table [{}]".format(self.table_name))
                resp = await client.create_table(**self.table_schema)
                if resp.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                    logger.info("DynamoDB table [{}] successfully created!".format(self.table_name))
                    return True
        except Exception as e:
            logger.error("[DB] Error when setting up DynamoDB.")
            logger.error(e)
        return False

    async def scan(self):
        scan_params = {
            "TableName": self.table_name,
            "Select": "ALL_ATTRIBUTES",
            "Limit": 5
        }
        db = await self.db
        try:
            response = await db.scan(**scan_params)
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                return response["Items"]
        except BotoCoreError as e:
            logger.error("[DB] Error when scanning db")
            logger.error(e)
        return []

    async def insert_post(self, **kwargs):
        params = {
            "TableName": self.table_name,
            "Item": {
                "target_id": {"S": kwargs.get("target_id")},
                "post_id": {"S": str(kwargs.get("post_id"))},
                "source_id": {"S": kwargs.get("source_id")},
                "text":  {"S": kwargs.get("text") or " "},
                "sticky": {"N": str(int(kwargs.get("sticky", False)))},
                "created": {"S": datetime.strftime(kwargs.get("created"), self.date_fmt)},
                "updated": {"S": datetime.strftime(kwargs.get("updated"), self.date_fmt)},
            }
        }
        # add doc at target if present
        if kwargs.get("target_doc"):
            params["Item"]["target_doc"] = {"S": json.dumps(kwargs["target_doc"])}
        db = await self.db
        try:
            response = await db.put_item(**params)
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                logger.info("[DB] Post {} {} was saved!".format(kwargs["source_id"], kwargs["post_id"]))
                return True
        except BotoCoreError as e:
            logger.error("[DB] Error when saving {}".format(kwargs))
            logger.error(e)
        return False

    async def get_last_updated(self, source_id):
        params = {
            "TableName": self.table_name,
            "IndexName": "source_id-updated-index",
            "KeyConditionExpression": "source_id = :value",
            "ExpressionAttributeValues": {
                ":value": {"S": str(source_id)},
            },
            "ProjectionExpression": "source_id, updated, post_id",
            "ScanIndexForward": False,
            "Limit": 1,
        }
        db = await self.db
        try:
            response = await db.query(**params)
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                updated = response["Items"][0]["updated"]["S"] if response["Count"] == 1 else None
                tstamp = parse_date(updated) if updated else datetime.utcnow()
                return tstamp
        except BotoCoreError as e:
            logger.error("[DB] Error when querying for last updated item on {}".format(source_id))
            logger.error(e)
        return None

    async def get_post(self, target_id, post_id):
        params = {
            "TableName": self.table_name,
            "KeyConditionExpression": "target_id = :value AND post_id= :post_id",
            "ExpressionAttributeValues": {
                ":value": {"S": str(target_id)},
                ":post_id": {"S": str(post_id)}
            },
            "ScanIndexForward": False,
            "ProjectionExpression": "target_id, source_id, updated, post_id, target_doc, sticky",
        }
        db = await self.db
        try:
            response = await db.query(**params)
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                db_post = response["Items"][0] if response["Count"] >= 1 else None
                if db_post:
                    db_post["sticky"]     = db_post.get("sticky", {}).get("N")
                    db_post["updated"]    = db_post.get("updated", {}).get("S")
                    db_post["source_id"]  = db_post.get("source_id", {}).get("S")
                    db_post["post_id"]    = db_post.get("post_id", {}).get("S")
                    db_post["target_id"]  = db_post.get("target_id", {}).get("S")
                    db_post["target_doc"] = json.loads(db_post["target_doc"]["S"]) if db_post.get("target_doc",{}).get("S") else {}
                return db_post
        except BotoCoreError as e:
            logger.error("[DB] Error when querying for a post [{}] on {}".format(post_id, target_id))
            logger.error(e)
        return None

    async def update_post(self, **kwargs):
        try:
            db = await self.db
            target_id = kwargs.get("target_id")
            post_id = kwargs.get("post_id")
            if await self.delete_post(target_id, post_id) == True:
                await self.insert_post(**kwargs)
                logger.info("[DB] Post {} {} was updated!".format(target_id, post_id))
                return True
        except Exception as e:
            logger.error("[DB] Error when updating for a post [{}] on {}".format(kwargs.get("post_id"), kwargs.get("target_id")))
            logger.error(e)
        return False

    async def delete_post(self, target_id, post_id):
        params = {
            "TableName": self.table_name,
            "Key": {
                "target_id": {"S": str(target_id)},
                "post_id": {"S": str(post_id)},
            },
        }
        db = await self.db
        try:
            response = await db.delete_item(**params)
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                logger.info("[DB] Post {} {} was deleted!".format(target_id, post_id))
                return True
        except Exception as e:
            logger.error("[DB] Error when deleting for a post [{}] on {}".format(post_id, target_id))
            logger.error(e)
        return False
