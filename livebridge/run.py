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
import livebridge.logger
import signal
from livebridge import config
from livebridge.controller import Controller
from livebridge.components import get_db_client
from livebridge.loader import load_extensions

logger = logging.getLogger(__name__)


# clean up at tear down
async def finish(tasks):
    logger.info("Finishing ...")
    for t in tasks:
        logger.debug("... {}".format(t))
        t.cancel()
    logger.info("Bye!")


def main():
    # disable bot logging
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('websockets').setLevel(logging.INFO)

    # read cli args
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", required=True, help="Control file, can be path.")
    args = parser.parse_args()

    # get loop
    loop = asyncio.get_event_loop()

    # load extensions
    load_extensions()

    # setup db table
    db = get_db_client()
    loop.run_until_complete(db.setup())

    # Controller manages the tasks
    controller = Controller(config=config.AWS, control_file=args.control, poll_interval=config.POLL_INTERVAL)
    controller.run()

    # add signal handler
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), functools.partial(loop.stop))

    # run
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(controller.clean_shutdown())
        loop.run_until_complete(finish(controller.tasked))
        if loop._default_executor:
            loop._default_executor.shutdown(wait=True)
        loop.stop()
        loop.close()

