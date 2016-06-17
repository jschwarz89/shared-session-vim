import json
import logging
import os
import time
import selectors
import socket
import sys

import common
import leader

logger = logging.getLogger('ssvim')


class Client(object):
    def __init__(self, port, selector):
        self.port = port
        self.selector = selector
        self.socket = None

    def connect(self):
        retries = 3
        while retries:
            try:
                logger.info("Trying to connect to leader")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(('localhost', self.port))
                self.socket.setblocking(False)
                return True
            except ConnectionRefusedError:
                logger.error("Unable to connect to leader...")
                time.sleep(0.5)
                retries -= 1
        return False

    def run(self):
        if not self.connect():
            logger.info("Unable to connect!")
            sys.exit(1)

        logger.info("Connected to leader!")

        self.selector.register(self.socket, selectors.EVENT_READ,
                               self.read_socket)
        self.selector.register(sys.stdin, selectors.EVENT_READ,
                               self.read_stdin)

    def close(self):
        self.socket.close()
        self.selector.unregister(self.socket)
        self.selector.unregister(sys.stdin)

    def read_socket(self, socket):
        def failure_callback():
            logger.warning("Socket appears to be dead. Spawning leader!")
            self.close()
            leader.spawn(self.port)
            self.run()

        logger.info("starting to read from the server...")
        data = common.safe_recv(self.socket, failure_callback)
        if data:
            logger.debug("Writing to vim: %s" % data)
            print(data)
            sys.stdout.flush()

    def handle_vim_command(self, data):
        json_data = json.loads(data)
        if 'regcontents' in json_data:
            # This is a yank data
            register = json_data['regname']
            if not register:
                register = '"'
            content = os.linesep.join(json_data['regcontents'])
            if json_data['regtype'] == "V":
                content += os.linesep
            return ':let @%s="%s"' % (register, content)
        return data

    def read_stdin(self, stdin):
        data = input()
        logger.debug("Received command from vim: %s" % data)

        data = self.handle_vim_command(data) + os.linesep
        self.socket.send(data.encode())
