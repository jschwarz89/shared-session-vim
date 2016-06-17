#!/usr/bin/env python3

import functools
import logging
import selectors
import sys

from client import Client
import common
import leader

logger = logging.getLogger('ssvim')


def main():
    port = common.get_port()
    leader.spawn(port)

    common.setup_logging()
    logger.info("ssvim starting! :>")

    selector = selectors.DefaultSelector()
    client = Client(port, selector)
    client.run()

    while True:
        for key, mask in selector.select():
            callback = key.data
            callback(key.fileobj)

if __name__ == '__main__':
    main()
