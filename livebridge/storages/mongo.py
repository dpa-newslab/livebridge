# -*- coding: utf-8 -*-
#
# Copyright 2017 dpa-infocom GmbH
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
import dsnparse
import logging
from datetime import datetime
from pymongo import DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from livebridge.storages.base import BaseStorage


logger = logging.getLogger(__name__)


class MongoStorage(BaseStorage):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoStorage, cls).__new__(cls)
            logger.debug("MongoDB client: {}".format(cls._instance))
        return cls._instance

    def __init__(self, **kwargs):
        self.dsn = kwargs.get("dsn", None)
        self.table_name = kwargs.get("table_name")
        self.control_table_name = kwargs.get("control_table_name")

        # get db name
        info = dsnparse.parse(self.dsn)
        self.db_name = info.paths.pop() if len(info.paths) == 1 else ""
        assert self.db_name != "", "No database name provided in DSN connection string"

    @property
    async def db(self):
        if hasattr(self, "_db") and self._db:
            return self._db
        logger.debug("Connecting to {}".format(self.dsn))
        client = AsyncIOMotorClient(self.dsn)
        self._db = client[self.db_name]
        return self._db

    async def setup(self):
        """Setting up MongoDB collections, if they not exist."""
        try:
            db = await self.db
            collections = await db.collection_names()
            created = False
            if self.table_name not in collections:
                # create table
                logger.info("Creating MongoDB collection [{}]".format(self.table_name))
                await db.create_collection(self.table_name)
                await db[self.table_name].create_index([("target_id", DESCENDING), ("post_id", DESCENDING)])
                created = True
            # create control collection if not already created.
            if self.control_table_name not in collections:
                # create table
                logger.info("Creating MongoDB control data collection [{}]".format(self.control_table_name))
                await db.create_collection(self.control_table_name)
                created = True
            return created
        except Exception as exc:
            logger.error("[DB] Error when setting up MongoDB collections: {}".format(exc))
        return False

    async def get_last_updated(self, source_id):
        try:
            coll = (await self.db)[self.table_name]
            cursor = coll.find({"source_id": source_id})
            cursor.sort("updated", -1).limit(1)
            async for doc in cursor:
                if doc.get("updated"):
                    return doc["updated"]
        except Exception as exc:
            logger.error("[DB] Error when querying for last updated item on {}".format(source_id))
            logger.exception(exc)
        return None

    async def get_known_posts(self, source_id, post_ids):
        results = []
        try:
            object_ids = list(map(lambda x: ObjectId(x), post_ids))
            coll = (await self.db)[self.table_name]
            cursor = coll.find({"source_id": source_id, "_id": {"$in": object_ids}})
            async for doc in cursor:
                results.append(str(doc["_id"]))
        except Exception as exc:
            logger.error("[DB] Error when querying for posts {}".format(post_ids))
            logger.exception(exc)
        return results

    async def get_post(self, target_id, post_id):
        try:
            coll = (await self.db)[self.table_name]
            doc = await coll.find_one({"target_id": target_id, "post_id": post_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        except Exception as exc:
            logger.error("[DB] Error when querying for a post [{}] on {}".format(post_id, target_id))
            logger.error(exc)
        return None

    async def insert_post(self, **kwargs):
        try:
            target_id = kwargs.get("target_id")
            doc = {
                "target_id": target_id,
                "post_id": str(kwargs.get("post_id")),
                "source_id": kwargs.get("source_id"),
                "text": kwargs.get("text") or " ",
                "sticky": str(int(kwargs.get("sticky", False))),
                "created": kwargs.get("created"),
                "updated": kwargs.get("updated"),
                "target_id": target_id,
                "target_doc": kwargs.get("target_doc", "")
            }
            coll = (await self.db)[self.table_name]
            await coll.insert_one(doc)
            logger.info("[DB] Post {} {} was saved!".format(kwargs["source_id"], kwargs["post_id"]))
            return True
        except Exception as exc:
            logger.error("[DB] Error when saving {}".format(kwargs))
            logger.error(exc)
        return False

    async def update_post(self, **kwargs):
        try:
            target_id = kwargs.get("target_id")
            doc = {
                "target_id": target_id,
                "post_id": str(kwargs.get("post_id")),
                "source_id": kwargs.get("source_id"),
                "text": kwargs.get("text") or " ",
                "sticky": str(int(kwargs.get("sticky", 0))),
                "created": kwargs.get("created"),
                "updated": kwargs.get("updated"),
                "target_id": target_id,
                "target_doc": kwargs.get("target_doc", "")
            }
            coll = (await self.db)[self.table_name]
            await coll.replace_one({"target_id": kwargs.get("target_id"), "post_id": kwargs.get("post_id")}, doc)
            logger.info("[DB] Post {} {} was updated!".format(kwargs.get("post_id"), kwargs.get("target_id")))
            return True
        except Exception as exc:
            logger.error("[DB] Error when updating for a post [{}] on {}".format(
                kwargs.get("post_id"), kwargs.get("target_id")))
            logger.error(exc)
        return False

    async def delete_post(self, target_id, post_id):
        try:
            coll = (await self.db)[self.table_name]
            await coll.remove({"target_id": target_id, "post_id": post_id}, {"justOne": True})
            logger.info("[DB] Post {} {} was deleted!".format(target_id, post_id))
            return True
        except Exception as exc:
            logger.error("[DB] Error when deleting for a post [{}] on {}".format(post_id, target_id))
            logger.error(exc)
        return False

    async def get_control(self, updated=None):
        try:
            query = {"type": "control"}
            if updated:
                query["updated"] = {"$gt": updated}
            coll = (await self.db)[self.control_table_name]
            doc = await coll.find_one(query)
            if doc:
                return doc
        except Exception as exc:
            logger.error("[DB] Error when querying for a control data on {}".format(self.control_table_name))
            logger.error(exc)
        return False

    async def save_control(self, data):
        try:
            query = {"type": "control"}
            doc = {"type": "control", "data": data, "updated": datetime.now()}
            coll = (await self.db)[self.control_table_name]
            res = await coll.replace_one(query, doc, upsert=True)
            if res.modified_count != 1 and not res.upserted_id:
                logger.error("[DB] Control data was not saved.")
            else:
                logger.info("[DB] Control data was saved.")
                return True
        except Exception as exc:
            logger.error("[DB] Error when saving control data on {}".format(self.control_table_name))
            logger.error(exc)
        return False
