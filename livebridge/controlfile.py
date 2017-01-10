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
import copy
import os
import logging
import boto3
import yaml
from botocore.client import Config
from livebridge.config import AWS

logger = logging.getLogger(__name__)

class ControlFile(object):

    def __init__(self):
        pass

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

    def load(self, path, *, resolve_auth=False):
        if not path.startswith("s3://"):
            body = self.load_from_file(path)
        else:
            body = self.load_from_s3(path)
        control = yaml.load(body)

        # filter duplicates
        control = self._remove_doubles(control)

        if resolve_auth:
            control = self._resolve_auth(control)

        return control

    def load_from_file(self, path):
        logger.info("Loading control file from disk: {}".format(path))
        if not os.path.exists(path):
            raise IOError("Path for control file not found.")

        file = open(path, "r")
        body = file.read()
        file.close()

        return body

    def load_from_s3(self, url):
        bucket, key = url.split('/', 2)[-1].split('/', 1)
        logger.info("Loading control file from s3: {} - {}".format(bucket, key))
        config = Config(signature_version="s3v4") if AWS["region"] in ["eu-central-1"] else None
        client = boto3.client(
            's3',
            region_name=AWS["region"],
            aws_access_key_id=AWS["access_key"] or None,
            aws_secret_access_key=AWS["secret_key"] or None,
            config=config,
        )
        control_file = client.get_object(Bucket=bucket, Key=key)
        return control_file["Body"].read()
