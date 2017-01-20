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
import logging
from livebridge.components import get_converter, get_db_client


logger = logging.getLogger(__name__)


class BaseTarget(object):
    """Base class for targets.

    Every concrete implementation of a target, requires to implement following methods:

    * :func:`post_item` - creates new resource at target
    * :func:`delete_item` - deletes resoruce at target
    * :func:`update_item` - updates resource at target
    * :func:`handle_extras` - handle extra actions, for example set resource to *sticky* \
       at the target.

    If a method above is not needed, for example when no update is possible at the target, \
    use :func:`livebridge.posts.base.BasePost.get_action` to **ignore** this action."""
    __module__ = "livebridge.base"

    type = "base"

    def __init__(self, *, config={}, **kwargs):
        """Base constructor for targets.

        :param config: Configuration passed from the control file.
        """
        self.target_id = None

    @property
    def _db(self):
        if not hasattr(self, "_db_client") or getattr(self, "_db_client") is None:
            self._db_client = get_db_client()
        return self._db_client

    def post_item(self, post):
        """Creates new resource at target.

        :param post: - Object of type :class:`livebridge.posts.base.BasePost`
        :returns: - :class:`livebridge.base.TargetResponse` of the newly created resource returned \
        from service, empty if failed."""
        raise NotImplementedError()

    def delete_item(self, post):
        """Deletes an existing resource at target.

        :param post: - Object of type :class:`livebridge.posts.base.BasePost`
        :returns: - :class:`livebridge.base.TargetResponse` of the deleted resource \
        returned from service, empty or False if failed."""
        raise NotImplementedError()

    def update_item(self, post):
        """Updates existing resource resource at target.

        :param post: - Object of type :class:`livebridge.posts.base.BasePost`
        :returns: - :class:`livebridge.base.TargetResponse` of the updated resource \
        returned from service, empty or False if failed."""
        raise NotImplementedError()

    def handle_extras(self, post):
        """Handle extra actions, for example set resource to *sticky* at the target. Return None \
        if method is unneeded.

        :param post: - Object of type :class:`livebridge.posts.base.BasePost`
        :returns: - :class:`livebridge.base.TargetResponse` of the updated resource returned \
        from service, empty or None if nothing has changed at resource."""
        raise NotImplementedError()

    async def _handle_new(self, post):
        new_doc = await self.post_item(post)
        logger.debug("Target CREATE: {}".format(new_doc))
        if not new_doc:
            logger.error("Post {} wasn't saved in {}".format(post.id, self.target_id))
            return ""
        return new_doc

    async def _handle_delete(self, post):
        del_res = await self.delete_item(post)
        logger.debug("Target DELETE: {}".format(del_res))
        if not del_res:
            logger.error("Deleting post failed: [{}] on {}".format(post.id, post.target_id))
            return False
        await self._db.delete_post(
            post.target_id,
            post.id
        )
        logger.info("Deleted post: [{}] on {}".format(post.id, post.target_id))
        return True

    async def _handle_update(self, post):
        update_res = await self.update_item(post)
        logger.debug("Target UPDATE: {}".format(update_res))
        if not update_res:
            logger.error("Target Update failed {} / {}".format(post.id, post.content))

        logger.info("Updated post: [{}] on {}".format(post.id, post.target_id))
        return update_res

    def _get_converter(self, post):
        return get_converter(post.source, self.type)

    async def handle_post(self, post):
        # convert
        converter = self._get_converter(post)
        if converter:
            # convert from source to target
            conversion = await converter.convert(post.data)
            post.content = conversion.content
            post.images = conversion.images
            logger.debug("CONVERSION RESULTS: {}".format(post.content))

            if not post.content and not post.is_deleted:
                logger.warning("Empty text, post got ignored.")
                return None

        post.set_existing(await self._db.get_post(self.target_id, post.id))
        action = post.get_action()
        logger.info("POST ACTION: {} - {} - {}".format(action, self.target_id, post.id))
        if action == "ignore":
            return None
        elif action == "create":
            post.target_doc = await self._handle_new(post)
        elif action == "update":
            post.target_doc = await self._handle_update(post)
        elif action == "delete":
            await self._handle_delete(post)
            return None

        # handle extra traits of target
        extra_doc = await self.handle_extras(post)
        if extra_doc:
            # use updated doc from target
            post.target_doc = extra_doc

        if post:
            # save new doc
            put_params = {
                "target_id": self.target_id,
                "post_id": post.id,
                "source_id": post.source_id,
                "text": str(post.content),
                "sticky": post.is_sticky,
                "created": post.created,
                "updated": post.updated,
                "target_doc": post.target_doc.data,
            }
            if action == "create":
                await self._db.insert_post(**put_params)
            elif action == "update":
                await self._db.update_post(**put_params)

        # clean up converter images
        if converter:
            await converter.remove_images(post.images)
