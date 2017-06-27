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
from unittest.mock import MagicMock
from livebridge.components import get_post, add_post
from livebridge.base import BasePost
from tests import load_json

class MockPost(BasePost):
    source = "test"

class PostTest(unittest.TestCase):

    def setUp(self):
        self.post = MockPost({})
        add_post(MockPost)

    def test_parent_methods(self):
        with self.assertRaises(NotImplementedError):
            self.post.get_action()

        with self.assertRaises(NotImplementedError):
            self.post.id

        with self.assertRaises(NotImplementedError):
            self.post.source_id

        with self.assertRaises(NotImplementedError):
            self.post.created

        with self.assertRaises(NotImplementedError):
            self.post.updated

        with self.assertRaises(NotImplementedError):
            self.post.is_update

        with self.assertRaises(NotImplementedError):
            self.post.is_deleted

        with self.assertRaises(NotImplementedError):
            self.post.is_sticky

        with self.assertRaises(NotImplementedError):
            self.post.is_submitted

        with self.assertRaises(NotImplementedError):
            self.post.is_draft

    def test_get_post(self):
        images = ["/tmp/test.jsp"]
        content = "foobaz"
        api_doc = {"doc": "api"}
        source = MagicMock()
        source.type = "test"
        post = get_post(source, api_doc, content="foobaz", images=["/tmp/test.jsp"])
        assert type(post) == MockPost
        assert post.images == images
        assert post.content == content
        assert post.data == api_doc
        assert source.type ==  "test"

    def test_target_doc(self):
        assert self.post.target_doc == None
        self.post._existing = {"target_doc": {"doc": "foo"}}
        assert self.post.target_doc == self.post._existing["target_doc"]

    def test_target_doc_setter(self):
        assert self.post.target_doc == None
        self.post.target_doc = {"target_doc": {"doc": "foo"}}
        assert self.post.target_doc ==  {"target_doc": {"doc": "foo"}}

    def test_target_id(self):
        # from existing doc
        assert self.post._target_id == None
        self.post._existing = {"target_id": "baz"}
        assert self.post.target_id == "baz"

        # from target_id
        self.post._target_id = "foobaz"
        assert self.post.target_id == "foobaz"

    def test_existing(self):
        assert self.post.get_existing() == None
        assert self.post.is_known == False
        self.post.set_existing({"foo": "baz"})
        assert self.post.get_existing() == {"foo": "baz"}
        assert self.post.is_known == True
