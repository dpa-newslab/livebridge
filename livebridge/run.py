# -*- coding: utf-8 -*-
#
# Copyright 2016, 2017 dpa-infocom GmbH
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
from livebridge.web import WebApi
from livebridge.loader import load_extensions


def read_args(**kwargs):
    """Read controlfile parameter."""
    if kwargs.get("control"):
        args = Namespace(control=kwargs["control"])
    elif config.CONTROLFILE:
        args = Namespace(control=config.CONTROLFILE)
    elif config.DB.get("control_table_name"):
        args = Namespace(control="sql")
    elif config.AWS.get("control_table_name"):
        args = Namespace(control="dynamodb")
    else:
        # read cli args
        parser = argparse.ArgumentParser()
        parser.add_argument("--control", required=True, help="Control file, can be path.")
        args = parser.parse_args()
    return args


def main(**kwargs):
    # disable bot logging
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('websockets').setLevel(logging.INFO)

    # read args
    args = read_args(**kwargs)

    # initialize loop
    loop = asyncio.get_event_loop() if not kwargs.get("loop") else kwargs["loop"]

    # load extensions
    load_extensions()

    # setup db table
    db_connector = get_db_client()
    loop.run_until_complete(db_connector.setup())

    # controller manages the tasks / data
    controller = Controller(config=config, control_file=args.control)
    asyncio.ensure_future(controller.run())

    # start http api
    if config.WEB.get("host") and config.WEB.get("port"):
        server = WebApi(config=config.WEB, controller=controller, loop=loop)

    # add signal handler
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), functools.partial(loop.stop))

    lb = LiveBridge(loop=loop, controller=controller)

    if kwargs.get("loop"):
        return lb

    # run
    try:
        loop.run_forever()
    finally:
        if config.WEB.get("host") and config.WEB.get("port"):
            server.shutdown()
        lb.shutdown()
        loop.stop()
        loop.close()
