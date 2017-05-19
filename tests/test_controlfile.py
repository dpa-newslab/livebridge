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
import botocore
import unittest
import unittest.mock
import os.path
import yaml
from io import StringIO
from livebridge.controlfile import ControlFile

from tests import load_file


class ControlTest(unittest.TestCase):

    def setUp(self):
        self.yaml_str = load_file("control.yaml")
        self.control = ControlFile()

    def test_load_from_file_no_exists(self):
        self.assertRaises(IOError, self.control.load, "/home/baz/control.yaml")

    def test_load_from_file(self):
        assert self.control.control_data == {}
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        control = self.control.load(file_path)
        assert set(self.control.control_data.keys()) == set(["bridges", "auth"])
        assert control["auth"]["dev"]["api_key"] == "F00Baz"
        assert control["auth"]["live"]["api_key"] == "Foobar"
        assert control["bridges"][0]["source_id"] == "abcdefg"
        assert control["bridges"][0]["type"] == "liveblog"
        assert control["bridges"][0]["endpoint"] ==  "https://example.com/api/"
        assert control["bridges"][0]["targets"][0]["event_id"] == "123456"
        assert control["bridges"][0]["targets"][0]["type"] == "scribble"
        assert control["bridges"][0]["targets"][0]["auth"] == "dev"
        assert control["bridges"][0]["targets"][1]["event_id"] == "654321"
        assert control["bridges"][0]["targets"][1]["type"] == "another"
        assert control["bridges"][0]["targets"][1]["auth"] == "live"
        assert control["bridges"][1]["source_id"] == 54321
        assert control["bridges"][1]["endpoint"] == "https://foo.org/api/"
        assert control["bridges"][1]["type"] == "liveblog"
        assert control["bridges"][1]["targets"][0]["event_id"] == "123456"
        assert control["bridges"][1]["targets"][0]["type"] == "scribble"
        assert control["bridges"][1]["targets"][0]["auth"] == "dev"

    def test_load_auth_resolved(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        yaml_str = open(file_path).read()
        self.control.load_from_file = lambda x: yaml_str
        control = self.control.load(file_path, resolve_auth=True)

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

    def test_load_auth_resolved_failed(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        yaml_str = open(file_path).read().replace("dev:", "dev_who:")
        self.control.load_from_file = lambda x: yaml_str
        self.assertRaises(LookupError, self.control.load, file_path, resolve_auth=True)

    def test_load_by_s3_url(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        yaml_str = open(file_path).read()
        self.control.load_from_s3 = lambda x: yaml_str
        control = self.control.load("s3://foobaz/control.yaml", resolve_auth=True)

        assert control["auth"]["dev"]["api_key"] == "F00Baz"
        assert control["auth"]["live"]["api_key"] == "Foobar"

    def test_load_from_s3(self):
        s3_url = "s3://foobaz/control.yaml"
        mock_client = unittest.mock.Mock()
        mock_client.get_object.return_value = {"Body":StringIO("foo")}
        with unittest.mock.patch("boto3.client") as patched:
            patched.return_value = mock_client
            control_data = self.control.load_from_s3(s3_url)
            assert control_data == "foo"
            assert patched.call_count == 1
            assert patched.call_args[0] == ('s3',)
            assert patched.call_args[1]["region_name"] == "eu-central-1"
            assert type(patched.call_args[1]["config"]) == botocore.config.Config
            mock_client.get_object.assert_called_once_with(Bucket='foobaz', Key='control.yaml')

    def test_controlfile_without_auth(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-no-auth.yaml")
        control = self.control.load(file_path, resolve_auth=True)
        assert 1 == True

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

    def test_iter_bridges(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        control = self.control.load(file_path)
        bridges = self.control.list_bridges()
        assert len(bridges) == 2
