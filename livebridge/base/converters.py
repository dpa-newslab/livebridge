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
import aiohttp
import logging
import os.path
import uuid

logger = logging.getLogger(__name__)

FILE_EXT = {
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "image/png": "png",
}

class BaseConverter(object):
    """Base class for converters.

    Concrete implementations have to implement public :func:`convert` method."""
    __module__ = "livebridge.base"

    source = ""
    target = ""

    def __init__(self):
        pass

    async def _download_image(self, data):
        filename = "{}-{}.{}".format(
            str(uuid.uuid4())[:8],
            data["media"],
            FILE_EXT[data["mimetype"]]
        )
        filepath = os.path.join("/tmp/", filename)
        with aiohttp.ClientSession() as session:
            async with session.get(data["href"]) as resp:
                test = await resp.read()
                with open(filepath, "wb") as f:
                    f.write(test)
        return filepath

    async def remove_images(self, images):
        try:
            for filepath in images:
                os.remove(filepath)
                logger.info("Removed image {}".format(filepath))
        except Exception as e:
            logger.error("Error when deleting image.")
            logger.exception(e)

    async def convert(self, post):
        """Convert incoming content of the incoming post to a string suitable to the \
           target as content.

           :param post: post object
           :type post: livebridge.posts.base.BasePost
           :returns: string - result of the conversion as string."""
        raise NotImplementedError("Not implemented in converter.")
