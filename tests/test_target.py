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
import asynctest
import livebridge.components
from unittest.mock import MagicMock
from livebridge.base import BaseTarget, BaseConverter, TargetResponse
from livebridge.storages import DynamoClient
from livebridge.components import get_target, add_target


class TestTarget(BaseTarget):
    type = "test"
    def __init__(self, *, config={}, **kwargs):
        self.foo = config.get("foo")


class BaseTargetTests(asynctest.TestCase):

    def setUp(self):
        self.converter = BaseConverter
        self.converter.convert = asynctest.CoroutineMock(return_value=("converted", []))
        self.converter.remove_images = asynctest.CoroutineMock(return_value=True)
        self.converter.source = "liveblog"
        self.converter.target = "scribble"
        livebridge.components.add_converter(self.converter)

        self.target= BaseTarget()
        self.target.type = "test"
        self.target.target_id = "test-target"
        self.target._get_converter = MagicMock(return_value=self.converter)
        self.target._db.get_post = asynctest.CoroutineMock(return_value=True)

        self.post = MagicMock()
        self.post.id = "123456"
        self.post.target_id = "post-target"
        self.post.content = ""

    @asynctest.ignore_loop
    def test_get_target(self):
        target = TestTarget
        add_target(target)
        conf = {"type": target.type, "foo": "baz"}
        new_target = get_target(conf)
        assert new_target.type == target.type
        assert new_target.foo == conf["foo"]

    @asynctest.ignore_loop
    def test_get_target_unkown(self):
        target = get_target({"type": "foo"})
        assert target == None

    @asynctest.ignore_loop
    def test_init(self):
        assert isinstance(self.target._db, DynamoClient) == True
        assert isinstance(self.target, BaseTarget) == True

    @asynctest.ignore_loop
    def test_db(self):
        self.target._db_client =  "foo"
        assert self.target._db ==  "foo"

        # poperty not set
        del self.target._db_client
        assert isinstance(self.target._db, DynamoClient) == True

    @asynctest.ignore_loop
    def test_parent_methods(self):
        with self.assertRaises(NotImplementedError):
            self.target.post_item(self.post)

        with self.assertRaises(NotImplementedError):
            self.target.delete_item(self.post)

        with self.assertRaises(NotImplementedError):
            self.target.update_item(self.post)

        with self.assertRaises(NotImplementedError):
            self.target.handle_extras(self.post)

    @asynctest.ignore_loop
    def test_get_converter(self):
        target = BaseTarget()
        self.post.source = "liveblog"
        target.type = "scribble"
        res = target._get_converter(self.post)
        assert type(res) == self.converter
        assert res.source == self.converter.source
        assert res.target == self.converter.target

    async def test_handle_post_ignore(self):
        self.post.get_action = MagicMock(return_value="ignore")
        self.target.handle_extras = asynctest.CoroutineMock(return_value=None)
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._get_converter.assert_called_once_with(self.post)
        self.target.handle_extras.called == 0

    async def test_handle_post_create(self):
        new_doc = TargetResponse({"doc": "foo"})
        self.post.get_action = MagicMock(return_value="create")
        self.target._handle_new = asynctest.CoroutineMock(return_value=new_doc)
        self.target.handle_extras = asynctest.CoroutineMock(return_value=None)
        self.target._db.insert_post = asynctest.CoroutineMock(return_value=None)

        assert self.post.content == ""
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._handle_new.assert_called_once_with(self.post)
        self.target.handle_extras.assert_called_once_with(self.post)
        self.target._db.get_post.assert_called_once_with(self.target.target_id, self.post.id)
        assert self.target._db.insert_post.call_count ==  1
        self.target._get_converter.assert_called_once_with(self.post)
        assert self.converter.convert.call_count == 1
        assert self.post.content == "converted"

    async def test_handle_post_without_converter(self):
        new_doc = TargetResponse({"doc": "foo"})
        self.post.get_action = MagicMock(return_value="create")
        self.target._handle_new = asynctest.CoroutineMock(return_value=new_doc)
        self.target.handle_extras = asynctest.CoroutineMock(return_value=None)
        self.target._db.insert_post = asynctest.CoroutineMock(return_value=None)
        self.target._get_converter = MagicMock(return_value=None)

        assert self.post.content == ""
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._handle_new.assert_called_once_with(self.post)
        self.target.handle_extras.assert_called_once_with(self.post)
        self.target._db.get_post.assert_called_once_with(self.target.target_id, self.post.id)
        assert self.target._db.insert_post.call_count ==  1
        self.target._get_converter.assert_called_once_with(self.post)
        assert self.converter.convert.call_count == 0
        assert self.converter.remove_images.call_count == 0
        assert self.post.content == ""

    async def test_handle_post_extras(self):
        new_doc = TargetResponse({"doc": "foo"})
        extras_doc = TargetResponse({"doc": "foo", "extras": 1})
        self.post.get_action = MagicMock(return_value="create")
        self.target._handle_new = asynctest.CoroutineMock(return_value=new_doc)
        self.target.handle_extras = asynctest.CoroutineMock(return_value=extras_doc)
        self.target._db.insert_post = asynctest.CoroutineMock(return_value=None)
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._handle_new.assert_called_once_with(self.post)
        self.target.handle_extras.assert_called_once_with(self.post)
        assert self.target._db.insert_post.call_count ==  1

    async def test_handle_post_update(self):
        new_doc = TargetResponse({"doc": "foo"})
        self.post.get_action = MagicMock(return_value="update")
        self.target._handle_update = asynctest.CoroutineMock(return_value=new_doc)
        self.target.handle_extras = asynctest.CoroutineMock(return_value=None)
        self.target._db.update_post = asynctest.CoroutineMock(return_value=None)
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._handle_update.assert_called_once_with(self.post)
        self.target.handle_extras.assert_called_once_with(self.post)
        self.target._db.get_post.assert_called_once_with(self.target.target_id, self.post.id)
        self.target._get_converter.assert_called_once_with(self.post)
        assert self.target._db.update_post.call_count ==  1

    async def test_handle_post_delete(self):
        self.post.get_action = MagicMock(return_value="delete")
        self.target._handle_delete = asynctest.CoroutineMock(return_value={})
        self.target.handle_extras = asynctest.CoroutineMock(return_value=None)
        res = await self.target.handle_post(self.post)
        assert res == None
        self.target._handle_delete.assert_called_once_with(self.post)
        self.target.handle_extras.called == 0
        self.target._db.get_post.assert_called_once_with(self.target.target_id, self.post.id)
        self.target._get_converter.assert_called_once_with(self.post)

    async def test_handle_post_failing(self):
        self.post.is_deleted = False
        self.converter.convert = asynctest.CoroutineMock(return_value=(None,[]))
        res = await self.target.handle_post(self.post)
        assert res == None

    async def test_handle_new(self):
        new_doc = {"doc": "foo"}
        self.target.post_item =  asynctest.CoroutineMock(return_value=new_doc)
        res = await self.target._handle_new(self.post)
        assert res == new_doc

    async def test_handle_new_failing(self):
        self.target.post_item =  asynctest.CoroutineMock(return_value={})
        res = await self.target._handle_new(self.post)
        assert res == ""

    async def test_handle_delete(self):
        new_doc = {"doc": "foo"}
        self.target.delete_item = asynctest.CoroutineMock(return_value=new_doc)
        self.target._db.delete_post =  asynctest.CoroutineMock()
        res = await self.target._handle_delete(self.post)
        assert res == True
        self.target.delete_item.assert_called_once_with(self.post)
        self.target._db.delete_post.assert_called_once_with(self.post.target_id, self.post.id)

    async def test_handle_delete_failing(self):
        self.target.delete_item = asynctest.CoroutineMock(return_value=None)
        self.target._db.delete_post = asynctest.CoroutineMock()
        res = await self.target._handle_delete(self.post)
        assert res == False
        self.target.delete_item.assert_called_once_with(self.post)
        assert self.target._db.delete_post.call_count == 0

    async def test_handle_update(self):
        new_doc = {"doc": "foo", "update": 1}
        self.target.update_item = asynctest.CoroutineMock(return_value=new_doc)
        res = await self.target._handle_update(self.post)
        assert res == new_doc
        self.target.update_item.assert_called_once_with(self.post)

    async def test_handle_update_failing_id_at_target(self):
        self.target.update_item = asynctest.CoroutineMock(return_value={})
        res = await self.target._handle_update(self.post)
        assert res == {}
        self.target.update_item.call_count == 1

    async def test_handle_update_failingupdate_item(self):
        self.target.update_item = asynctest.CoroutineMock(return_value={})
        res = await self.target._handle_update(self.post)
        assert res == {}
        self.target.update_item.call_count == 1
        self.target.update_item.assert_called_once_with(self.post)
