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
import os
import json
from livebridge.components import get_db_client


def load_file(name):
    file_path = os.path.join(os.path.dirname(__file__), "files", name)

    f = open(file_path)
    body = f.read()
    f.close()

    return body


def load_json(name):
    return json.loads(load_file(name))


def get_dynamo_client(access_key, secret_key, region, endpoint_url, table_name="livebridge_test"):
        return get_db_client(
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            endpoint_url=endpoint_url,
            table_name=table_name)
