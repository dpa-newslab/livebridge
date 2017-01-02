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
import logging
import sys

from livebridge.config import LOGFILE, LOGLEVEL

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOGLEVEL))
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s %(message)s')

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

if LOGFILE:
    fh = logging.FileHandler(LOGFILE)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
