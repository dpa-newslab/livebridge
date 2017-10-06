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
import hashlib
import logging
from livebridge import config
from livebridge.storages import DynamoClient, SQLStorage, MongoStorage, DummyStorage


logger = logging.getLogger(__name__)


SOURCE_MAP = {}
CONVERTER_MAP = {}
POST_MAP = {}
TARGET_MAP = {}


def get_source(conf):
    client = None
    if SOURCE_MAP.get(conf.get("type")):
        source_cls = SOURCE_MAP[conf.get("type")]
        client = source_cls(config=conf)
    else:
        logger.warning("No source client found for {}.".format(conf))
    return client


def add_source(cls):
    SOURCE_MAP[cls.type] = cls


def get_converter(source, target):
    try:
        return CONVERTER_MAP[source][target]()
    except KeyError:
        logger.debug("no converter found for {} -> {}".format(source, target))
    return None


def add_converter(cls):
    CONVERTER_MAP.setdefault(cls.source, {})
    CONVERTER_MAP[cls.source][cls.target] = cls


def get_post(source, doc, content, images):
    return POST_MAP[source.type](doc, content=content, images=images)


def add_post(cls):
    POST_MAP[cls.source] = cls


def get_target(conf):
    client = None

    if TARGET_MAP.get(conf.get("type")):
        target_cls = TARGET_MAP[conf.get("type")]
        client = target_cls(config=conf)
    else:
        logger.warning("No target client found for {}.".format(conf))
    return client


def add_target(cls):
    TARGET_MAP[cls.type] = cls


def get_db_client(**kwargs):
    dsn = kwargs.get("dsn") or config.DB.get("dsn")
    if dsn:
        params = config.DB if not kwargs else kwargs
        if dsn.startswith("mongodb://"):
            return MongoStorage(**params)
        elif dsn.startswith("dummy://"):
            return DummyStorage(**params)
        else:
            return SQLStorage(**params)
    # default dynamodb
    params = config.AWS if not kwargs else kwargs
    return DynamoClient(**params)


def get_hash(data):
    return hashlib.md5(str(data).encode("utf-8")).hexdigest()
