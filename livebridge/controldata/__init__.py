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
from collections import OrderedDict
from livebridge.controldata.controlfile import ControlFile
from livebridge.controldata.dynamo import DynamoControl
from livebridge.controldata.storage import StorageControl

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
        self.new_bridges = []
        self.removed_bridges = []

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

        # detect changes
        self.new_bridges = [OrderedDict(n) for n in control_data.get("bridges", [])
                            if n not in self.control_data.get("bridges", [])]
        self.removed_bridges = [OrderedDict(r) for r in self.control_data.get("bridges", [])
                                if r not in control_data.get("bridges", [])]
        self.control_data = control_data

    async def save(self, path, data):
        if self.control_client is None:
            await self._set_client(path)
        return await self.control_client.save(path, data)

    def list_new_bridges(self):
        return self.new_bridges

    def list_removed_bridges(self):
        return self.removed_bridges

    def list_bridges(self):
        return self.control_data.get("bridges", [])

    def is_auto_update(self):
        return self.control_client.auto_update

    async def check_control_change(self, control_path):
        return await self.control_client.check_control_change(control_path=control_path)
