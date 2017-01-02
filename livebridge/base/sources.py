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
from livebridge.components import get_db_client


logger = logging.getLogger(__name__)


class BaseSource(object):
    """Base class for sources."""
    __module__ = "livebridge.base"

    type = ""
    mode = ""

    def __init__(self, *, config={}, **kwargs):
        """Base constructor for sources.

        :param config: Configuration passed from the control file.
        """
        pass

    @property
    def _db(self):
        """Database client for accessing storage.

           :returns: :class:`livebridge.storages.base.BaseStorage` """
        if not hasattr(self, "_db_client") or getattr(self, "_db_client") is None:
            self._db_client = get_db_client()
        return self._db_client

    async def filter_new_posts(self, source_id, post_ids):
        """Filters ist of post_id for new ones.

        :param source_id: id of the source
        :type string:
        :param post_ids: list of post ids
        :type list:
        :returns: list of unknown post ids."""
        new_ids = []
        try:
            db_client = self._db
            posts_in_db = await db_client.get_known_posts(source_id, post_ids)
            new_ids = [p for p in post_ids if p not in posts_in_db]
        except Exception as exc:
            logger.error("Error when filtering for new posts {} {}".format(source_id, post_ids))
            logger.exception(exc)
        return new_ids

    async def get_last_updated(self, source_id):
        """Returns latest update-timestamp from storage for source.

        :param source_id: id of the source (source_id, ticker_id, blog_id pp)
        :type string:
        :returns: :py:class:`datetime.datetime` object of latest update datetime in db."""
        last_updated = await self._db.get_last_updated(source_id)
        logger.info("LAST UPDATED: {} {}".format(last_updated, self))
        return last_updated


class PollingSource(BaseSource):
    """Base class for sources which are getting polled. Any custom adapter source, which \
       should get polled, has to be inherited from this base class."""

    mode = "polling"

    async def poll(self):
        """Method has to be implemented by the concrete inherited source class.

        :func:`poll` gets called by the interval defined by environment var *POLLING_INTERVALL*.

        The inheriting class has to implement the actual poll request for the source in this method.

        :return: list of new posts"""
        raise NotImplementedError("Method 'poll' not implemented.")


class StreamingSource(BaseSource):
    """Base class for streaming sources. Any custom adapter source, which is using a websocket, SSE or\
       any other stream as source has to be inherited from this base class."""

    mode = "streaming"

    async def listen(self, callback):
        """Method has to be implemented by the concrete inherited source class.

        A websocket connection has to be opened and given *callback* method has to be
        called with the new post as argument.

        :param callback: Callback method which has to be called with list of new posts.
        :return: True"""
        raise NotImplementedError("Method 'listen' not implemented.")

    async def stop(self):
        """Method has to be implemented by the concrete inherited source class.

           By calling this method, the websocket-connection has to be stopped.

           :return: True"""
        raise NotImplementedError("Method 'stop' not implemented.")
