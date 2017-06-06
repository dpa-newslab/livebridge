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
import os
import warnings

LOGLEVEL = os.environ.get("LB_LOGLEVEL", "INFO")

LOGFILE = os.environ.get("LB_LOGFILE")

CONTROLFILE = os.environ.get("LB_CONTROLFILE")

POLL_INTERVAL = int(os.environ.get("LB_POLL_INTERVAL", 60))

DB = {
    "dsn": os.environ.get("LB_DB_DSN"),
    "table_name": os.environ.get("LB_DB_TABLE", "livebridge_dev"),
    "control_table_name": os.environ.get("LB_DB_CONTROL_TABLE", "livebridge_dev_control")
}

AWS = {
    "access_key": os.environ.get("LB_AWS_ACCESS_KEY", ""),
    "secret_key": os.environ.get("LB_AWS_SECRET_KEY", ""),
    "region":  os.environ.get("LB_AWS_REGION", "eu-central-1"),
    "endpoint_url": os.environ.get("LB_DYNAMO_ENDPOINT"),
    "table_name": os.environ.get("LB_DYNAMO_TABLE", "livebridge-dev"),
    "control_table_name": os.environ.get("LB_DYNAMO_CONTROL_TABLE"),
    "sqs_s3_queue": os.environ.get("LB_SQS_S3_QUEUE", ""),
}

if AWS.get("table_name"):
    warnings.simplefilter('default', DeprecationWarning)
    warnings.warn("LB_DYNAMO_TABLE is deprecated, use LB_DB_TABLE instead!", DeprecationWarning)
    DB["table_name"] = AWS["table_name"]
    del AWS["table_name"]
    warnings.simplefilter('ignore', DeprecationWarning)
