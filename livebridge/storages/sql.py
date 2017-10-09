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
import json
import logging
from datetime import datetime
from sqlalchemy_aio import ASYNCIO_STRATEGY
from sqlalchemy import create_engine, MetaData, Table, Column,\
    Integer, String, Text, Boolean, DateTime
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import select
from livebridge.storages.base import BaseStorage


logger = logging.getLogger(__name__)


class SQLStorage(BaseStorage):
    """
    http://docs.sqlalchemy.org/en/latest/core/engines.html
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SQLStorage, cls).__new__(cls)
            logger.debug("SQL client: {}".format(cls._instance))
        return cls._instance

    def __init__(self, **kwargs):
        self.dsn = kwargs.get("dsn", None)
        self.table_name = kwargs.get("table_name")
        self.control_table_name = kwargs.get("control_table_name")

    @property
    async def db(self):
        if hasattr(self, "_engine") and self._engine:
            return self._engine
        logger.debug("Connecting to {}".format(self.dsn))
        self._engine = create_engine(self.dsn, strategy=ASYNCIO_STRATEGY)
        return self._engine

    def _get_table(self):
        return Table(self.table_name, MetaData(),
                     Column("id", Integer(), primary_key=True),
                     Column("target_id", String(150), index=True),
                     Column("post_id", String(150), index=True),
                     Column("source_id", String(150), index=True),
                     Column("sticky", Boolean()),
                     Column("text", Text()),
                     Column("created", DateTime()),
                     Column("updated", DateTime(), index=True),
                     Column("target_doc", Text()))

    def _get_control_table(self):
        return Table(self.control_table_name, MetaData(),
                     Column("id", Integer(), primary_key=True),
                     Column("type", String(150), index=True),
                     Column("data", Text()),
                     Column("updated", DateTime()))

    async def setup(self):
        """Setting up SQL table, if it not exists."""
        try:
            engine = await self.db
            created = False
            if not await engine.has_table(self.table_name):
                # create table
                logger.info("Creating SQL table [{}]".format(self.table_name))
                items = self._get_table()
                await engine.execute(CreateTable(items))
                # create indeces
                conn = await engine.connect()
                await conn.execute(
                    "CREATE INDEX `lb_last_updated` ON `{}` (`source_id` DESC,`updated` DESC);".format(self.table_name))
                await conn.execute(
                    "CREATE INDEX `lb_post` ON `{}` (`target_id` DESC,`post_id` DESC);".format(self.table_name))
                await conn.close()
                created = True
            # create control table if not already created.
            if self.control_table_name and not await engine.has_table(self.control_table_name):
                # create table
                logger.info("Creating SQL control table [{}]".format(self.control_table_name))
                items = self._get_control_table()
                await engine.execute(CreateTable(items))
                created = True
            return created
        except Exception as exc:
            logger.error("[DB] Error when setting up SQL table: {}".format(exc))
        return False

    async def get_last_updated(self, source_id):
        try:
            db = await self.db
            table = self._get_table()
            result = await db.execute(
                table.select().where(
                    table.c.source_id == source_id
                ).order_by(
                    table.c.updated.desc()
                ).limit(1))
            item = await result.first()
            tstamp = item["updated"] if item else None
            return tstamp
        except Exception as exc:
            logger.error("[DB] Error when querying for last updated item on {}".format(source_id))
            logger.exception(exc)
        return None

    async def get_known_posts(self, source_id, post_ids):
        results = []
        try:
            db = await self.db
            table = self._get_table()
            sql = select(columns=[table.c.post_id]).where(table.c.source_id == source_id).where(
                table.c.post_id.in_(post_ids))
            db_res = await db.execute(sql)
            for row in await db_res.fetchall():
                results.append(row[0])
        except Exception as exc:
            logger.error("[DB] Error when querying for posts {}".format(post_ids))
            logger.exception(exc)
        return results

    async def get_post(self, target_id, post_id):
        try:
            db = await self.db
            table = self._get_table()
            sql = table.select().where(table.c.target_id == target_id).where(table.c.post_id == post_id).limit(1)
            result = await db.execute(sql)
            item = await result.first()
            if item:
                item = dict(item)
                item["target_doc"] = json.loads(item["target_doc"]) if item.get("target_doc") != "" else {}
            return item
        except Exception as exc:
            logger.error("[DB] Error when querying for a post [{}] on {}".format(post_id, target_id))
            logger.error(exc)
        return None

    async def insert_post(self, **kwargs):
        try:
            db = await self.db
            table = self._get_table()
            sql = table.insert().values(
                target_id=kwargs.get("target_id"),
                post_id=kwargs.get("post_id"),
                source_id=kwargs.get("source_id"),
                text=kwargs.get("text"),
                sticky=int(kwargs.get("sticky", "0")),
                created=kwargs.get("created"),
                updated=kwargs.get("updated"),
                target_doc=json.dumps(kwargs.get("target_doc")) if kwargs.get("target_doc") else ""
            )
            await db.execute(sql)
            logger.info("[DB] Post {} {} was saved!".format(kwargs["source_id"], kwargs["post_id"]))
            return True
        except Exception as exc:
            logger.error("[DB] Error when saving {}".format(kwargs))
            logger.error(exc)
        return False

    async def update_post(self, **kwargs):
        try:
            db = await self.db
            table = self._get_table()
            sql = table.update().where(
                table.c.target_id == kwargs.get("target_id")
            ).where(
                table.c.post_id == kwargs.get("post_id")
            ).values(
                target_id=kwargs.get("target_id"),
                post_id=kwargs.get("post_id"),
                source_id=kwargs.get("source_id"),
                text=kwargs.get("text"),
                sticky=int(kwargs.get("sticky", "0")),
                created=kwargs.get("created"),
                updated=kwargs.get("updated"),
                target_doc=json.dumps(kwargs.get("target_doc")) if kwargs.get("target_doc") else ""
            )
            await db.execute(sql)
            logger.info("[DB] Post {} {} was updated!".format(kwargs.get("post_id"), kwargs.get("target_id")))
            return True
        except Exception as exc:
            logger.error("[DB] Error when updating for a post [{}] on {}".format(
                kwargs.get("post_id"), kwargs.get("target_id")))
            logger.error(exc)
        return False

    async def delete_post(self, target_id, post_id):
        try:
            db = await self.db
            table = self._get_table()
            sql = table.delete().where(table.c.target_id == target_id).where(table.c.post_id == post_id)
            await db.execute(sql)
            logger.info("[DB] Post {} {} was deleted!".format(target_id, post_id))
            return True
        except Exception as exc:
            logger.error("[DB] Error when deleting for a post [{}] on {}".format(post_id, target_id))
            logger.error(exc)
        return False

    async def get_control(self, updated=None):
        try:
            db = await self.db
            table = self._get_control_table()
            sql = table.select().where(table.c.type == "control")
            if updated:  # check for updated timestamp
                sql = sql.where(table.c.updated != updated)
            sql = sql.limit(1)
            result = await db.execute(sql)
            item = await result.first()
            if item:
                item = dict(item)
                item["data"] = json.loads(item["data"]) if item.get("data") != "" else {}
                return item
        except Exception as exc:
            logger.error("[DB] Error when querying for a control data on {}".format(self.control_table_name))
            logger.error(exc)
        return False

    async def save_control(self, data):
        try:
            db = await self.db
            table = self._get_control_table()
            existing = await self.get_control()
            updated = datetime.now()
            if existing:
                # update
                sql = table.update().where(table.c.type == "control").values(
                    data=json.dumps(data),
                    updated=updated
                )
            else:
                # create
                sql = table.insert().values(
                    type="control",
                    data=json.dumps(data),
                    updated=updated
                )
            await db.execute(sql)
            logger.info("[DB] Control data was saved.")
            return True
        except Exception as exc:
            logger.error("[DB] Error when saving control data on {}".format(self.control_table_name))
            logger.error(exc)
        return False
