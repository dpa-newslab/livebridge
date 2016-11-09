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
import unittest
import os.path
import yaml
from livebridge.controlfile import ControlFile

from tests import load_file


class ControlTest(unittest.TestCase):

    def setUp(self):
        self.yaml_str = load_file("control.yaml")
        self.control = ControlFile()

    def test_load_from_file_no_exists(self):
        self.assertRaises(IOError, self.control.load, "/home/baz/control.yaml")

    def test_load_from_file(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        control = self.control.load(file_path)

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

    def test_controlfile_without_auth(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-no-auth.yaml")
        control = self.control.load(file_path, resolve_auth=True)
        print(control)
        assert 1 == True
