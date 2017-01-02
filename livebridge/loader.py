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
import pkgutil
import inspect
import logging
from importlib import import_module
from livebridge.base import BaseTarget, BasePost, BaseSource, BaseConverter
from livebridge.components import add_converter, add_post, add_target, add_source

logger = logging.getLogger(__name__)


def load_extensions():
    for pkg_info in pkgutil.walk_packages(onerror=importfail):
        if pkg_info[1].startswith("livebridge"):
            if pkg_info[2] is True:
                get_extensions(pkg_info)


def importfail(pkg):
    """Just do nothing when module-walk fails."""
    pass


def get_extensions(pkg):
    mod = import_module(pkg[1])
    for member in [d for d in inspect.getmembers(mod) if not d[0].startswith("__") and inspect.isclass(d[1])]:
        ext = member[1]
        if issubclass(ext, BaseTarget):
            logger.debug("Loading target: {}".format(ext))
            add_target(ext)
        elif issubclass(ext, BaseSource):
            logger.debug("Loading source: {}".format(ext))
            add_source(ext)
        elif issubclass(ext, BasePost):
            logger.debug("Loading post: {}".format(ext))
            add_post(ext)
        elif issubclass(ext, BaseConverter):
            logger.debug("Loading converter: {}".format(ext))
            add_converter(ext)
