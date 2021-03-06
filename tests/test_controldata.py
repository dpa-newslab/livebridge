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
import os
from livebridge.controldata import ControlData
from livebridge.controldata.base import BaseControl
from livebridge.controldata.controlfile import ControlFile
from livebridge.controldata.storage import StorageControl


class BaseControlTest(asynctest.TestCase):

    def setUp(self):
        self.base = BaseControl()

    async def test_check_control_change(self):
        with self.assertRaises(NotImplementedError):
            await self.base.check_control_change()

    async def test_load(self):
        with self.assertRaises(NotImplementedError):
            await self.base.load("path")

    async def test_close(self):
        assert await self.base.close() == None

class ControlDataTests(asynctest.TestCase):

    def setUp(self):
        self.config = {
            "access_key": "foo",
            "secret_key": "baz",
            "region": "eu-central-1",
            "sqs_s3_queue": "http://foo-queue",
        }
        self.control = ControlData(self.config)

    async def test_set_client(self):
        await self.control._set_client(path="file")
        assert type(self.control.control_client) == ControlFile

        await self.control._set_client(path="sql")
        assert type(self.control.control_client) == StorageControl

    async def test_check_control_change(self):
        control_client = asynctest.MagicMock()
        control_client.check_control_change = asynctest.CoroutineMock(return_value=True)
        self.control.control_client = control_client
        res = await self.control.check_control_change(control_path="/foo")
        assert res is True
        assert control_client.check_control_change.call_count == 1
        assert control_client.check_control_change.call_args == asynctest.call(control_path="/foo")

    async def test_iter_bridges(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        await self.control.load(file_path)
        bridges = self.control.list_bridges()
        assert len(bridges) == 2
        for b in bridges:
            assert "source_id" in b
            assert "targets" in b

    async def test_load_dynamo(self):
        self.control.CONTROL_DATA_CLIENTS["dynamodb"].load = \
            asynctest.CoroutineMock(return_value={"auth": {}, "bridges": []})
        await self.control.load("dynamodb")
        assert self.control.control_data == {'auth': {}, 'bridges': []}

    async def test_load_auth_resolved(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        await self.control.load(file_path, resolve_auth=True)

        control = self.control.control_data
        assert control["auth"]["dev"]["api_key"] == "F00Baz"
        assert control["auth"]["live"]["api_key"] == "Foobar"
        assert control["bridges"][0]["source_id"] == "abcdefg"
        assert control["bridges"][0]["endpoint"] == "https://example.com/api/"
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

    async def test_load_auth_env_auth_resolved(self):
        os.environ["LB_FOO_USER"] = "foo-user"
        os.environ["LB_BAR_TOKEN"] = "bar.token"
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-env-notation.yaml")
        await self.control.load(file_path, resolve_auth=True)

        control = self.control.control_data
        assert control["auth"]["foo"]["user"] == os.environ["LB_FOO_USER"]
        assert control["auth"]["foo"]["pwd"] == "env.LB_NOT_DEFINED"
        assert control["auth"]["bar"]["token"] == os.environ["LB_BAR_TOKEN"]
        assert control["auth"]["bar"]["key"] == "env.NO_VALID_NAME"
        # check nested auth isn't resolved
        assert control["auth"]["foo"]["nested"] == {"foo": "env.LB_FOO_USER"}

    @asynctest.fail_on(unused_loop=False)
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
                }
            ],
            'auth': {
                'dev': {'api_key': 'F00Baz', 'user': 'dev', 'password': 'pwd'},
                'slack': {'token': 'token-str'},
                'live': {'api_key': 'Foobar', 'user': 'prod', 'password': 'pwd2'}
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

    async def test_load_detect_changes(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-changes-old.yaml")
        await self.control.load(file_path, resolve_auth=True)

        assert len(self.control.new_bridges) > 0
        assert len(self.control.removed_bridges) == 0

        file_path = os.path.join(os.path.dirname(__file__), "files", "control-changes-new.yaml")
        await self.control.load(file_path, resolve_auth=True)
        assert len(self.control.new_bridges) == 1
        assert len(self.control.removed_bridges) == 1
        assert self.control.removed_bridges == self.control.list_removed_bridges()

    async def test_load_control_doc_sorted(self):
        sorted_doc = {
            "auth":{},
            "bridges":[
                {"a":"b", "c":"d", "e":"f", "g":"h", "targets":[]},
                {"i":"j", "k":"l", "m":"n", "o":"p", "targets":[]}
            ]
        }
        doc_data = {
            "auth":{},
            "bridges":[
                {"g":"h", "c":"d", "e":"f", "a":"b", "targets":[]},
                {"targets":[], "m":"n", "i":"j", "o":"p", "k":"l"}
            ]
        }
        self.control.control_client = asynctest.MagicMock(spec=ControlFile)
        self.control.control_client.load = asynctest.CoroutineMock(return_value=doc_data)
        data = await self.control.load_control_doc("/tmp/foo")
        assert self.control.control_client.load.call_count == 1
        assert data == sorted_doc

    async def test_save(self):
        self.control.control_client = asynctest.MagicMock(spec=ControlFile)
        self.control.control_client.save.return_value = True
        path = "/tmp/foo"
        data = {"foo": "baz"}
        res = await self.control.save(path, data)
        assert res is True
        assert self.control.control_client.save.call_count == 1

    @asynctest.fail_on(unused_loop=False)
    def test_remove_inactives(self):
        doc1 = {
            "auth":{"foo":{"user":"foo", "pwd": "baz"}},
            "bridges": [
                {"label": "One", "active": False},
                {"label": "Two", "active": True},
                {"label": "Three"},
            ]}
        res = self.control._remove_inactives(doc1)
        assert res == {
            "auth":{"foo":{"user":"foo", "pwd": "baz"}},
            "bridges": [
                {"label": "Two", "active": True},
                {"label": "Three"},
            ]}

    @asynctest.fail_on(unused_loop=False)
    def test_list_new_bridges(self):
        self.control.new_bridges = ["foo", "bar"]
        assert self.control.list_new_bridges() == ["foo", "bar"]

    @asynctest.fail_on(unused_loop=False)
    def test_list_removed_bridges(self):
        self.control.removed_bridges = ["foo", "baz"]
        assert self.control.list_removed_bridges() == ["foo", "baz"]

    async def test_auto_update(self):
        self.control.control_client = ControlFile()
        assert self.control.control_client.auto_update is True
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        await self.control.control_client.load(file_path)
        assert self.control.control_client.auto_update is False
        assert self.control.is_auto_update() is False

        await self.control._set_client(path="sql")
        assert self.control.is_auto_update() is True
