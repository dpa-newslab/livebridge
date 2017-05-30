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
import botocore
import asynctest
import unittest
import unittest.mock
import os.path
import yaml
from io import StringIO
from botocore.exceptions import ClientError
from livebridge.controldata.controlfile import ControlFile

from tests import load_file


class ControlFileTest(asynctest.TestCase):

    def setUp(self):
        self.yaml_str = load_file("control.yaml")
        self.control = ControlFile()
        self.control.config = {
            "access_key": "foo",
            "secret_key": "baz",
            "region":  "eu-central-1",
            "sqs_s3_queue": "http://foo-queue",
        }

        # set mock clients
        self.control._sqs_client = unittest.mock.MagicMock()

    async def test_sqs_client(self):
        client = await self.control.sqs_client
        assert self.control._sqs_client == client

    async def test_new_sqs_client(self):
        self.control._sqs_client = None
        self.control._purge_sqs_queue = asynctest.CoroutineMock(return_value=True)
        mock_sqs_client = asynctest.MagicMock()
        mock_session = unittest.mock.MagicMock()
        mock_session.create_client = unittest.mock.MagicMock(return_value=mock_sqs_client)
        with asynctest.patch("aiobotocore.get_session") as patched:
            patched.return_value = mock_session
            client = await self.control.sqs_client
            assert mock_session.create_client.call_count == 1
            assert mock_session.create_client.call_args[0] == ("sqs",)
            assert mock_session.create_client.call_args[1]["region_name"] == "eu-central-1"
            assert client == mock_sqs_client
            assert client == self.control._sqs_client
            assert self.control._purge_sqs_queue.call_count == 1

    async def test_purge_sqs_queue(self):
        self.control._sqs_client = asynctest.MagicMock()
        self.control._sqs_client.purge_queue = asynctest.CoroutineMock(return_value=True)
        await self.control._purge_sqs_queue()
        assert self.control._sqs_client.purge_queue.call_count == 1
        assert self.control._sqs_client.purge_queue.call_args == \
                    asynctest.call(QueueUrl='http://foo-queue')

    async def test_purge_sqs_queue_failing(self):
        self.control._sqs_client = asynctest.MagicMock()
        self.control._sqs_client.purge_queue = asynctest.CoroutineMock(
            side_effect=[ClientError({"Error": {"Code": 1, "Message": "Testerror"}}, operation_name="foo")])
        await self.control._purge_sqs_queue()
        assert self.control._sqs_client.purge_queue.call_count == 1
        assert self.control._sqs_client.purge_queue.call_args == \
                    asynctest.call(QueueUrl='http://foo-queue')

    @asynctest.ignore_loop
    def test_del(self):
        self.control._sqs_client.close = asynctest.CoroutineMock()
        self.control.__del__()
        assert self.control._sqs_client.close.call_count == 1

    async def test_load_from_file_no_exists(self):
        with self.assertRaises(IOError):
            await self.control.load("/home/baz/control.yaml")

    async def test_load_from_file(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        control_data = await self.control.load(file_path)
        assert set(control_data.keys()) == set(["bridges", "auth"])
        assert control_data["auth"]["dev"]["api_key"] == "F00Baz"
        assert control_data["auth"]["live"]["api_key"] == "Foobar"
        assert control_data["bridges"][0]["source_id"] == "abcdefg"
        assert control_data["bridges"][0]["type"] == "liveblog"
        assert control_data["bridges"][0]["endpoint"] ==  "https://example.com/api/"
        assert control_data["bridges"][0]["targets"][0]["event_id"] == "123456"
        assert control_data["bridges"][0]["targets"][0]["type"] == "scribble"
        assert control_data["bridges"][0]["targets"][0]["auth"] == "dev"
        assert control_data["bridges"][0]["targets"][1]["event_id"] == "654321"
        assert control_data["bridges"][0]["targets"][1]["type"] == "another"
        assert control_data["bridges"][0]["targets"][1]["auth"] == "live"
        assert control_data["bridges"][1]["source_id"] == 54321
        assert control_data["bridges"][1]["endpoint"] == "https://foo.org/api/"
        assert control_data["bridges"][1]["type"] == "liveblog"
        assert control_data["bridges"][1]["targets"][0]["event_id"] == "123456"
        assert control_data["bridges"][1]["targets"][0]["type"] == "scribble"
        assert control_data["bridges"][1]["targets"][0]["auth"] == "dev"

    async def test_load_by_s3_url(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control.yaml")
        yaml_str = open(file_path).read()
        self.control._load_from_s3 = lambda x: yaml_str
        control = await self.control.load("s3://foobaz/control.yaml", resolve_auth=True)

        assert control["auth"]["dev"]["api_key"] == "F00Baz"
        assert control["auth"]["live"]["api_key"] == "Foobar"

    @asynctest.ignore_loop
    def test_load_from_s3(self):
        s3_url = "s3://foobaz/control.yaml"
        mock_client = unittest.mock.Mock()
        mock_client.get_object.return_value = {"Body":StringIO("foo")}
        with unittest.mock.patch("boto3.client") as patched:
            patched.return_value = mock_client
            control_data = self.control._load_from_s3(s3_url)
            assert control_data == "foo"
            assert patched.call_count == 1
            assert patched.call_args[0] == ('s3',)
            assert patched.call_args[1]["region_name"] == "eu-central-1"
            assert type(patched.call_args[1]["config"]) == botocore.config.Config
            mock_client.get_object.assert_called_once_with(Bucket='foobaz', Key='control.yaml')

    async def test_controlfile_without_auth(self):
        file_path = os.path.join(os.path.dirname(__file__), "files", "control-no-auth.yaml")
        control = await self.control.load(file_path, resolve_auth=True)
        assert 1 == True

    async def test_check_control_change(self):
        messages = {"Messages": [{"Body": '{"Records": []}', "ReceiptHandle": "baz"}]}
        sqs_client = asynctest.MagicMock()
        sqs_client.purge_queue = asynctest.CoroutineMock(return_value=None)
        sqs_client.receive_message = asynctest.CoroutineMock(return_value=messages)
        sqs_client.delete_message = asynctest.CoroutineMock(return_value=True)
        self.control._sqs_client = sqs_client
        await self.control.check_control_change()
        sqs_client.receive_message.assert_called_once_with(
            QueueUrl=self.control.config["sqs_s3_queue"])
        sqs_client.delete_message.assert_called_once_with(
            QueueUrl=self.control.config["sqs_s3_queue"],
            ReceiptHandle="baz")

    async def test_check_control_change_with_exception(self):
        sqs_client = asynctest.MagicMock()
        sqs_client.purge_queue = asynctest.CoroutineMock(return_value=None)
        sqs_client.receive_message = asynctest.CoroutineMock(side_effect=[Exception()])
        self.control._sqs_client = sqs_client
        await self.control.check_control_change()
        sqs_client.receive_message.assert_called_once_with(
            QueueUrl=self.control.config["sqs_s3_queue"])

    async def test_check_control_change_with_records(self):
        messages = {"Messages": [{"Body": '{"Records": [{"foo":"baz"}]}', "ReceiptHandle": "baz"}]}
        sqs_client = asynctest.MagicMock()
        sqs_client.purge_queue = asynctest.CoroutineMock(
            side_effect=[ClientError({"Error": {"Code": 1, "Message": "Testerror"}}, operation_name="foo")])
        sqs_client.receive_message = asynctest.CoroutineMock(return_value=messages)
        sqs_client.delete_message = asynctest.CoroutineMock(return_value=True)
        self.control._sqs_client = sqs_client
        res = await self.control.check_control_change()
        assert res == True
