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


class BasePost(object):
    """Base class for posts.

    Every concrete implementation of this base class have to implement the \
    poperties defined here. This is needed, so the specific targets do not have \
    to differentiate by the post type, but rather have a unified way to access \
    common properties from the resource, regardless of their source."""
    __module__ = "livebridge.base"

    source = ""

    def __init__(self, data, *, content="", images=[]):
        """Base constructor for targets.

        :param data: - dictionary of source post data
        :param content: - string of convertered post content, optional
        :param images: - list of iage_paths, optional"""
        self.data = data
        self.content = content
        self.images = images
        self._existing = None
        self._target_id = None
        self._target_doc = None

    @property
    def id(self):
        """Returns the id of the resource at its source."""
        raise NotImplementedError("Property not implemented.")

    @property
    def source_id(self):
        """Returns the id of the source. For example the id of the blog polled."""
        raise NotImplementedError("Property not implemented.")

    @property
    def created(self):
        """Returns created datetime of the resource, has to be a :py:class:`datetime.datetime` object."""
        raise NotImplementedError("Property not implemented.")

    @property
    def updated(self):
        """Returns updated datetime of the resource, has to be a :py:class:`datetime.datetime` object."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_update(self):
        """Returns boolean if resource is updated or not."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_deleted(self):
        """Returns boolean if resource is deleted or not."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_sticky(self):
        """Returns boolean if resource is sticky or not."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_submitted(self):
        """Returns boolean if resource is in submitted state."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_draft(self):
        """Returns boolean if resource is in drafted state."""
        raise NotImplementedError("Property not implemented.")

    @property
    def is_known(self):
        """Returns boolean if resource is already known to livebridge."""
        return bool(self._existing)

    def get_action(self):
        """Returns type of action which has to be handled by the target.
           Can be either **create**, **update**, **delete** or **ignore**."""
        raise NotImplementedError("Method not implemented.")

    @property
    def target_doc(self):
        """Returns resource doc as at the target, when the posting was already created \
           at the target. This property normally contains the **target_doc** data from \
           the livebrigde storage item, saved in a syndication earlier.

        :returns: dict"""
        if not hasattr(self, "_target_doc") or not self._target_doc:
            if self._existing:
                self._target_doc = self._existing.get("target_doc", {})
        return self._target_doc

    @target_doc.setter
    def target_doc(self, value):
        """Setter method for **target_doc** property."""
        self._target_doc = value

    @property
    def target_id(self):
        """Returns the id the target, to which this post has to be syndicated.

        :returns: string"""
        # already set?
        if self._target_id:
            return self._target_id
        # post already exists?
        if self._existing:
            self._target_id = self._existing.get("target_id")
        return self._target_id

    def set_existing(self, existing):
        """Takes existing doc at target.

        :param existing: - dict, resource doc at target."""
        self._existing = existing

    def get_existing(self):
        """Returns existing resource at target.

        :returns: - dict of resource"""
        return self._existing
