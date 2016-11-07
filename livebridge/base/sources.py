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
