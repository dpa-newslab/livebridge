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

    @property
    async def db(self):
        raise NotImplementedError()

    def setup(self):
        raise NotImplementedError()

    async def insert_post(self, **kwargs):
        raise NotImplementedError()

    async def get_post(self, target_id, post_id):
        raise NotImplementedError()

    async def update_post(self, target_id, post_id, ):
        raise NotImplementedError()

    async def delete_post(self, target_id, post_id):
        raise NotImplementedError()

    async def get_last_updated(self, source_id):
        raise NotImplementedError()

    async def get_known_posts(self, source_id, post_ids):
        """Return a list of known post_id of a source for a given list of post ids.

        :param source_id: id of the source
        :type string:
        :param post_ids: list of post ids
        :type list:
        :returns: - list of dictionaries."""
        raise NotImplementedError()
