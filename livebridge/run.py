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
import argparse
import asyncio
import functools
import logging
import signal
import livebridge.logger
from argparse import Namespace
from livebridge import config, LiveBridge
from livebridge.controller import Controller
from livebridge.components import get_db_client
from livebridge.loader import load_extensions


def main(loop=None, **kwargs):
    # disable bot logging
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('websockets').setLevel(logging.INFO)

    # check for controlfile parameter
    if kwargs.get("control"):
        args = Namespace(control=kwargs["control"])
    elif config.CONTROLFILE:
        args = Namespace(control=config.CONTROLFILE)
    else:
        # read cli args
        parser = argparse.ArgumentParser()
        parser.add_argument("--control", required=True, help="Control file, can be path.")
        args = parser.parse_args()

    if not loop:
        loop = asyncio.get_event_loop()

    # load extensions
    load_extensions()

    # setup db table
    db_connector = get_db_client()
    loop.run_until_complete(db_connector.setup())

    # Controller manages the tasks
    controller = Controller(config=config.AWS, control_file=args.control, poll_interval=config.POLL_INTERVAL)
    controller.run()

    # add signal handler
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), functools.partial(loop.stop))

    livebridge = LiveBridge(loop=loop, controller=controller)

    if kwargs.get("loop"):
        return livebridge

    # run
    try:
        loop.run_forever()
    finally:
        livebridge.shutdown()
        loop.stop()
        loop.close()
