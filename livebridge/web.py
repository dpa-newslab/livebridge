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
import asyncio
import logging
from aiohttp import web


logger = logging.getLogger(__name__)


class WebApi(object):

    def __init__(self, *, controller, loop):
        self.loop = loop
        self.app = web.Application()
        self.app["controller"] = controller
        self._add_routes()
        self.handler = self.app.make_handler()
        f = self.loop.create_server(self.handler, '0.0.0.0', 8080)
        self.srv = loop.run_until_complete(f)

    def _add_routes(self):
        self.app.router.add_get("/", self.index_handler)
        self.app.router.add_get("/api/v1/controlfile", self.control_get)
        self.app.router.add_post("/api/v1/controlfile", self.control_post)

    async def index_handler(self, request):
        return web.json_response({})

    async def control_get(self, request):
        return web.json_response({"foo": "GET"})

    async def control_post(self, request):
        return web.json_response({"foo": "POST"})

    def shutdown(self):
        logger.debug("Shutting down web API!")
        self.srv.close()
        self.loop.run_until_complete(self.srv.wait_closed())
        self.loop.run_until_complete(self.app.shutdown())
        self.loop.run_until_complete(self.handler.shutdown(60.0))
        self.loop.run_until_complete(self.app.cleanup())
