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
import logging
import uuid
from aiohttp import web

logger = logging.getLogger(__name__)

_tokens = {}


async def auth_middleware(app, handler):
    async def middleware_handler(request):
        try:
            # check auth header
            if not request.path == "/api/v1/session":
                token = request.headers.get("X-Auth-Token")
                if token not in _tokens.values():
                    return web.json_response({"error": "Invalid token."}, status=401)
            # return response
            response = await handler(request)
            return response
        except web.HTTPException as ex:
            raise
    return middleware_handler


def error_overrides(overrides):
    async def middleware(app, handler):
        async def middleware_handler(request):
            try:
                response = await handler(request)
                return response
            except web.HTTPException as ex:
                override = overrides.get(ex.status)
                if override:
                    return await override(request, ex)
        return middleware_handler
    return middleware


class WebApi(object):

    def __init__(self, *, config, controller, loop):
        self.config = config
        self.loop = loop

        # start server
        logger.info("Starting API server ...")
        middlewares = [error_overrides({405: self.handle_405}), auth_middleware]
        self.app = web.Application(loop=loop, middlewares=middlewares)
        self.app["controller"] = controller
        self.app.router.add_get("/", self.index_handler)
        self.app.router.add_get("/api/v1/controldata", self.control_get)
        self.app.router.add_put("/api/v1/controldata", self.control_put)
        self.app.router.add_post("/api/v1/session", self.login, expect_handler=web.Request.json)
        self.handler = self.app.make_handler()
        f = self.loop.create_server(self.handler, self.config["host"], self.config["port"])
        self.srv = loop.run_until_complete(f) if not loop.is_running() else None
        logger.info("... API server started up")

    async def login(self, request):
        try:
            assert self.config["auth"]["user"]
            assert self.config["auth"]["password"]
        except AssertionError:
            logger.error("HTTP Auth credentials are missing!")
            return web.json_response({"error": "Auth credentials are missing."}, status=400)

        params = await request.post()
        user = params.get('username', None)
        if (user == self.config["auth"]["user"] and
                params.get('password', None) == self.config["auth"]["password"]):
            # User is in our database, remember their login details
            _tokens[user] = str(uuid.uuid4())
            return web.json_response({"token": _tokens[user]})
        return web.json_response({"error": "Unauthorized"}, status=401)

    async def handle_405(self, request, response):
        return web.json_response({"error": "Method Not Allowed"}, status=405)

    async def index_handler(self, request):
        return web.json_response({})

    async def control_get(self, request):
        control_data = await self.app["controller"].load_control_data(resolve_auth=False)
        return web.json_response(control_data.control_data)

    async def control_put(self, request):
        try:
            await request.post()
            if request.has_body:
                uploaded_doc = await request.json()
                res = await self.app["controller"].save_control_data(uploaded_doc)
                if res:
                    return web.json_response({"ok": "true"})
                else:
                    return web.json_response({"error": "Controldata was not saved."}, status=400)
            else:
                return web.json_response({"error": "No request body was found."}, status=400)

        except Exception as exc:
            logger.error("Error handling PUT controldata")
            logger.exception(exc)
            return web.json_response({"error": "Internal Server Error"}, status=500)

    def shutdown(self):
        logger.debug("Shutting down web API!")
        if self.srv:
            self.srv.close()
        self.loop.run_until_complete(self.srv.wait_closed())
        self.loop.run_until_complete(self.app.shutdown())
        self.loop.run_until_complete(self.handler.shutdown(60.0))
        self.loop.run_until_complete(self.app.cleanup())
