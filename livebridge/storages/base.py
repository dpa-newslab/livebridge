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


class BaseStorage(object):
    """Base class for storage clients.

    Every concrete implementation of a storage class, requires to implement following methods:

    * :func:`db` - property holds underlying databse client.
    * :func:`setup` - Method for setting up storage, creating table pp.
    * :func:`insert_post` - insert single post into storage.
    * :func:`get_post` - returns single post from storage.
    * :func:`update_post` - updates single post in storage.
    * :func:`delete_post` - deletes single post in storage.
    * :func:`get_last_updated` - returns latest updated-timestamp or source from storage.
    """

    @property
    async def db(self):
        """Property holds underlying database client."""
        raise NotImplementedError()

    def setup(self):
        """Method for setting up storage, creating table pp."""
        raise NotImplementedError()

    async def insert_post(self, **kwargs):
        """Insert single post into storage."""
        raise NotImplementedError()

    async def get_post(self, target_id, post_id):
        """Returns single post from storage.

        :param target_id: id of the target
        :type string:
        :param post_id: id of post
        :type string:"""
        raise NotImplementedError()

    async def update_post(self, **kwargs):
        """Updates single post in storage."""
        raise NotImplementedError()

    async def delete_post(self, target_id, post_id):
        """Deletes single post from storage.

        :param target_id: id of the target
        :type string:
        :param post_id: id of post to delete
        :type string:"""
        raise NotImplementedError()

    async def get_last_updated(self, source_id):
        """Returns latest updated-timestamp of source from storage.

        :param source_id: id of the source
        :type string:"""
        raise NotImplementedError()

    async def get_known_posts(self, source_id, post_ids):
        """Return a list of known post_id of a source for a given list of post ids.

        :param source_id: id of the source
        :type string:
        :param post_ids: list of post ids
        :type list:
        :returns: - list of dictionaries."""
        raise NotImplementedError()

    async def get_control(self):
        """Method for retrieving of control data form storage.

        :returns: - dictionary"""
        raise NotImplementedError()

    async def save_control(self, data):
        """Method for saving control data in storage.

        :param data: control_data
        :type dict:
        :returns: - boolean"""
        raise NotImplementedError()
