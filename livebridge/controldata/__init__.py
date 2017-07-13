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
import copy
import logging
from livebridge.controldata.controlfile import ControlFile
from livebridge.controldata.dynamo import DynamoControl
from livebridge.controldata.storage  import StorageControl

logger = logging.getLogger(__name__)

class ControlData(object):

    CONTROL_DATA_CLIENTS = {
        "file": ControlFile,
        "dynamodb": DynamoControl,
        "sql": StorageControl,
    }

    def __init__(self, config):
        self.config = config
        self.control_client = None
        self.control_data = {}

    def _resolve_auth(self, data):
        for x, bridge in enumerate(data.get("bridges", [])):
            if data.get("auth", {}).get(bridge.get("auth")):
                # add user creds to bridge config
                data["bridges"][x]["auth"] = data["auth"][bridge["auth"]]
            for y, target in enumerate(bridge.get("targets", [])):
                if data.get("auth", {}).get(target.get("auth")):
                    # add user creds to target config
                    data["bridges"][x]["targets"][y]["auth"] = data["auth"][target["auth"]]
                elif target.get("auth"):
                    raise LookupError("Data for user [{}] not found in control file.".format(target.get("auth")))
        return data

    def _remove_doubles(self, control_data):
        bridges = []
        filtered = {"auth": control_data.get("auth", {}), "bridges": []}
        # clear double source->target connections
        for bridge in control_data.get("bridges", []):
            # filter sources
            source = copy.deepcopy(bridge)
            source["targets"] = []
            if source not in bridges:
                bridges.append(source)
                filtered["bridges"].append(copy.deepcopy(source))
            # filter targets
            for target in bridge.get("targets", []):
                index = bridges.index(source)
                if target not in filtered["bridges"][index]["targets"]:
                    filtered["bridges"][index]["targets"].append(target)
                else:
                    logger.info("Filtering double target [{}] from source [{}]".format(target, source))
        return filtered

    async def _set_client(self, path):
        if self.control_client:
            return self.control_client

        # set client for control data
        if self.CONTROL_DATA_CLIENTS.get(path):
            self.control_client = self.CONTROL_DATA_CLIENTS.get(path)()
        else:
            self.control_client = self.CONTROL_DATA_CLIENTS.get("file")()

    async def load(self, path, *, resolve_auth=False):
        control_data = {}
        await self._set_client(path)
        control_data = await self.control_client.load(path)

        # filter duplicates
        control_data = self._remove_doubles(control_data)

        if resolve_auth:
            control_data = self._resolve_auth(control_data)
        self.control_data = control_data

    async def save(self, path, data):
        await self._set_client(path)
        return await self.control_client.save(path, data)

    def list_bridges(self):
        return self.control_data.get("bridges", [])

    async def check_control_change(self, control_path):
        return await self.control_client.check_control_change(control_path=control_path)
