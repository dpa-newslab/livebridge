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
from collections import UserDict
from livebridge.base.sources import BaseSource, PollingSource, StreamingSource
from livebridge.base.targets import BaseTarget
from livebridge.base.posts import BasePost
from livebridge.base.converters import BaseConverter
from livebridge.components import get_converter, get_db_client


class TargetResponse(UserDict):
    """Data container for returning the resource data from a service, awaits dictionary.

    Data returned from a BaseTarget derived target type has to be a TargetResponse.
    """
    pass
