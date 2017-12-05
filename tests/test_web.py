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
import asynctest
import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from livebridge.web import WebApi


class WebApiTestCase(AioHTTPTestCase):

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        self.config = {
            "host": "localhost",
            "port": 9990,
            "auth": {"user": "test", "password": "testpwd"}}
        self.controller = asynctest.MagicMock(spec="livebridge.controller.Controller")
        self.server = WebApi(config=self.config, controller=self.controller, loop=self.loop)
        return self.server.app

    @unittest_run_loop
    async def test_init_with_loop(self):
        self.loop.is_running = unittest.mock.Mock(return_value=False)
        self.loop.run_until_complete = unittest.mock.Mock(return_value=False)
        f = asynctest.CoroutineMock(return_value={"foo": "baz"})
        self.loop.create_server = unittest.mock.Mock(return_value=f())
        server = WebApi(config=self.config, controller=self.controller, loop=self.loop)
        assert type(server) == WebApi
        assert self.loop.create_server.call_count == 1
        assert self.loop.create_server.call_args[0][0] == server.handler
        assert self.loop.create_server.call_args[0][1] == "localhost"
        assert self.loop.create_server.call_args[0][2] == 9990
        self.client.session.close()

    def test_shutdown(self):
        self.server.loop = unittest.mock.MagicMock()
        self.server.loop.run_until_complete = unittest.mock.MagicMock()
        self.server.srv = unittest.mock.MagicMock()
        self.server.srv.close = unittest.mock.MagicMock()
        self.server.shutdown()
        assert self.server.loop.run_until_complete.call_count == 4

    async def _get_token(self):
        data = {"username": self.config["auth"]["user"],
                "password": self.config["auth"]["password"]}
        request = await self.client.request("POST", "/api/v1/session", data=data)
        assert request.status == 200
        res = await request.json()
        assert res.get("token") is not None
        return res["token"]

    @unittest_run_loop
    async def test_unauthorized(self):
        urls = [
            ("GET", "/api/v1/controldata"),
            ("PUT", "/api/v1/controldata"),
        ]
        for u in urls:
            request = await self.client.request(u[0], u[1])
            assert request.status == 401
            text = await request.text()
            assert '{"error": "Invalid token."}' in text

    @unittest_run_loop
    async def test_open(self):
        urls = [
            ("GET", "/"),
            ("GET", "/dashboard"),
            ("GET", "/dashboard/lb.js"),
        ]
        for u in urls:
            request = await self.client.request(u[0], u[1])
            assert request.status == 200

    @unittest_run_loop
    async def test_login_failing(self):
        request = await self.client.request("GET", "/api/v1/session")
        assert request.status == 405
        assert (await request.json()) == {"error": "Method Not Allowed"}

        request = await self.client.request("POST", "/api/v1/session")
        assert request.status == 401

        data = {"username": self.config["auth"]["user"], "password": "foo"}
        request = await self.client.request("POST", "/api/v1/session", data=data)
        assert request.status == 401
        assert (await request.json()) == {"error": "Unauthorized"}

        self.config["auth"]["password"] = None
        request = await self.client.request("POST", "/api/v1/session", data=data)
        assert request.status == 400
        assert (await request.json()) == {"error": "Auth credentials are missing."}

    @unittest_run_loop
    async def test_login_token(self):
        token = await self._get_token()
        self.assertRegexpMatches(token, r'^[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}$')

    @unittest_run_loop
    async def test_get_controldata(self):
        doc = {"foo": "bla"}
        self.controller.load_control_doc = asynctest.CoroutineMock(return_value=doc)
        headers = {"X-Auth-Token": await self._get_token()}
        res = await self.client.request("GET", "/api/v1/controldata", headers=headers)
        assert res.status == 200
        assert (await res.json()) == doc

    @unittest_run_loop
    async def test_put_controldata(self):
        data = '{"foo": "bla"}'
        headers = {"X-Auth-Token": await self._get_token()}
        self.controller.save_control_data = asynctest.CoroutineMock(return_value=True)
        res = await self.client.request("PUT", "/api/v1/controldata", data=data, headers=headers)
        assert res.status == 200
        assert (await res.json()) == {"ok": "true"}
        assert self.controller.save_control_data.call_count == 1
        assert self.controller.save_control_data.call_args == asynctest.call({"foo": "bla"})

        # saving fails
        self.controller.save_control_data = asynctest.CoroutineMock(return_value=False)
        res = await self.client.request("PUT", "/api/v1/controldata", data=data, headers=headers)
        assert res.status == 400
        assert (await res.json()) == {"error": "Controldata was not saved."}
        assert self.controller.save_control_data.call_count == 1

        # no payload
        self.controller.save_control_data = asynctest.CoroutineMock(return_value=False)
        res = await self.client.request("PUT", "/api/v1/controldata", data=None, headers=headers)
        assert res.status == 400
        assert (await res.json()) == {"error": "No request body was found."}
        assert self.controller.save_control_data.call_count == 0

        # exception gets raised
        self.controller.save_control_data = asynctest.CoroutineMock(side_effect=Exception("Test-Error"))
        res = await self.client.request("PUT", "/api/v1/controldata", data=data, headers=headers)
        assert res.status == 500
        assert (await res.json()) == {"error": "Internal Server Error"}
        assert self.controller.save_control_data.call_count == 1
