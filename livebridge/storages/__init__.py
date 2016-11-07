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
from livebridge import config
from livebridge.storages.dynamo import DynamoClient
from livebridge.storages.sql import SQLStorage


def get_db_client(**kwargs):
    if kwargs.get("dsn") or config.DB.get("dsn"):
        params = config.DB if not kwargs else kwargs
        return SQLStorage(**params)
    # default dynamodb
    params = config.AWS if not kwargs else kwargs
    return DynamoClient(**params)