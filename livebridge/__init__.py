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
import logging
from collections import UserDict


log = logging.getLogger(__name__)


class LiveBridge(UserDict):
    """Livebridge object.

    :param loop: loop to use.
    :type :py:class:`asyncio.BaseEventLoop`
    :param controller: Livebridge controller
    :type :class:`livebridge.controller.Controller`
    """
    def __init__(self, loop, controller):
        self.loop = loop
        self.controller = controller

    # clean up at tear down
    async def finish(self, tasks):
        log.info("Finishing ...")
        for task in tasks:
            log.debug("... {}".format(task))
            if not task.exception():
                task.cancel()
        log.info("Bye!")

    def shutdown(self):
        self.loop.run_until_complete(self.controller.clean_shutdown())
        self.loop.run_until_complete(self.finish(self.controller.tasked))
        if self.loop._default_executor:
            self.loop._default_executor.shutdown(wait=True)
