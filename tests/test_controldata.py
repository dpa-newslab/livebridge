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
import os
import yaml
from livebridge.controldata import ControlData

class ControlDataTests(asynctest.TestCase):

    def setUp(self):
        self.config = {
            "access_key": "foo",
            "secret_key": "baz",
            "region":  "eu-central-1",
            "sqs_s3_queue": "http://foo-queue",
        }
        self.control = ControlData(self.config)

    async def test_check_control_change(self):
        control_client = asynctest.MagicMock()
        control_client.check_control_change = asynctest.CoroutineMock(return_value=True)
        self.control.control_client = control_client
        res = await self.control.check_control_change()
        assert res == True

    async def test_iter_bridges(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        control = await self.control.load(file_path)
        bridges = self.control.list_bridges()
        assert len(bridges) == 2
        for b in bridges:
            assert "source_id" in b
            assert "targets" in b

    async def test_load_auth_resolved(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        await self.control.load(file_path, resolve_auth=True)

        control = self.control.control_data
        assert control["auth"]["dev"]["api_key"] == "F00Baz"
        assert control["auth"]["live"]["api_key"] == "Foobar"
        assert control["bridges"][0]["source_id"] == "abcdefg"
        assert control["bridges"][0]["endpoint"] ==  "https://example.com/api/"
        assert control["bridges"][0]["type"] == "liveblog"
        assert control["bridges"][0]["targets"][0]["event_id"] == "123456"
        assert control["bridges"][0]["targets"][0]["type"] == "scribble"
        assert control["bridges"][0]["targets"][0]["auth"] == control["auth"]["dev"]
        assert control["bridges"][0]["targets"][1]["event_id"] == "654321"
        assert control["bridges"][0]["targets"][1]["type"] == "another"
        assert control["bridges"][0]["targets"][1]["auth"] == control["auth"]["live"]
        assert control["bridges"][1]["source_id"] == 54321
        assert control["bridges"][1]["endpoint"] == "https://foo.org/api/"
        assert control["bridges"][1]["type"] == "liveblog"
        assert control["bridges"][1]["auth"]["token"] == "token-str"
        assert control["bridges"][1]["targets"][0]["event_id"] == "123456"
        assert control["bridges"][1]["targets"][0]["type"] == "scribble"
        assert control["bridges"][1]["targets"][0]["auth"] == control["auth"]["dev"]

    async def test_load_auth_resolved_failed(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-lookup-error.yaml")
        with self.assertRaises(LookupError):
            await self.control.load(file_path, resolve_auth=True)

    @asynctest.ignore_loop
    def test_remove_doubles(self):
        control = {'bridges': [
            {
                'endpoint': 'https://example.com/api/',
                'type': 'liveblog',
                'targets': [
                        {'event_id': '123456', 'type': 'scribble', 'auth': 'dev'},
                        {'event_id': '654321', 'type': 'another', 'auth': 'live'},
                ],
                'source_id': 'abcdefg'
            }, {
                'source_id': "abcdef",
                'endpoint': 'https://another.org/api/',
                'type': 'foo',
                'targets': [
                    {'target_id': '123456', 'type': 'baz', 'auth': 'dev'},
                ],
            }, {
                'source_id': 54321,
                'endpoint': 'https://foo.org/api/',
                'type': 'liveblog',
                'targets': [
                    {'event_id': '123456', 'type': 'scribble', 'auth': 'dev'}],
                'auth': 'slack'
            }, {
                'endpoint': 'https://example.com/api/',
                'type': 'liveblog',
                'targets': [
                    {'event_id': '1122233', 'type': 'scribble', 'auth': 'dev'},
                    {'event_id': '123456', 'type': 'scribble', 'auth': 'dev'},
                    {'event_id': '654321', 'type': 'another', 'auth': 'live'},
                ],
                'source_id': 'abcdefg'
            }, {
                'source_id': 54321,
                'endpoint': 'https://foo.org/api/',
                'type': 'liveblog',
                'targets': [
                    {'event_id': '123456', 'type': 'scribble', 'auth': 'dev'},
                ],
                'auth': 'slack'
            }],
            'auth': {
                'dev': {'api_key': 'F00Baz', 'user': 'dev', 'password': 'pwd'},
                'slack': {'token': 'token-str'},
                'live': {'api_key': 'Foobar','user': 'prod','password': 'pwd2'}
            }
        }
        cleared = self.control._remove_doubles(control)
        assert len(cleared["bridges"]) == 3
        assert len(cleared["bridges"][0]["targets"]) == 3
        assert len(cleared["bridges"][1]["targets"]) == 1
        assert len(cleared["bridges"][2]["targets"]) == 1

        self.assertIn(control["bridges"][0]["targets"][0], cleared["bridges"][0]["targets"])
        self.assertIn(control["bridges"][0]["targets"][1], cleared["bridges"][0]["targets"])
        self.assertIn(control["bridges"][3]["targets"][0], cleared["bridges"][0]["targets"])
        self.assertIn(control["bridges"][3]["targets"][1], cleared["bridges"][0]["targets"])
        self.assertIn(control["bridges"][3]["targets"][1], cleared["bridges"][0]["targets"])

        self.assertIn(control["bridges"][1]["targets"][0], cleared["bridges"][1]["targets"])
        self.assertIn(control["bridges"][2]["targets"][0], cleared["bridges"][2]["targets"])
        self.assertIn(control["bridges"][4]["targets"][0], cleared["bridges"][2]["targets"])

        # test empty targets
        control["bridges"][4]["targets"] = []
        control["bridges"][2]["targets"] = []
        cleared = self.control._remove_doubles(control)
        assert len(cleared["bridges"]) == 3
        assert len(cleared["bridges"][0]["targets"]) == 3
        assert len(cleared["bridges"][1]["targets"]) == 1
        assert len(cleared["bridges"][2]["targets"]) == 0
