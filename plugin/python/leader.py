#!/usr/bin/env python3
import logging
import os
import selectors
import socket
import sys

import common
import vim_state

logger = logging.getLogger('ssvim')


class Leader(object):
    def __init__(self, port, selector):
        self.port = port
        self.selector = selector
        self.vim_state = vim_state.VimState()
        self.clients = []
        self.socket = None
        self.had_clients = False

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket.bind(('localhost', self.port))
        self.socket.listen(10)
        self.socket.setblocking(False)

        self.selector.register(self.socket, selectors.EVENT_READ,
                               self.server_callback)

        logger.info("Created leader successfully!")

    def close(self):
        for client in self.clients:
            client.close()
        self.socket.close()

    def server_callback(self, server_socket):
        (client, address) = self.socket.accept()
        logger.debug("New client connected: %s" % (address,))
        self.had_clients = True

        client.setblocking(False)
        self.clients.append(client)
        self.selector.register(client, selectors.EVENT_READ,
                               self.handle_socket_data)

    def handle_socket_data(self, joining_client):
        def failure_callback():
            logger.warning("Socket appears to be dead. Closing just in case.")
            joining_client.close()
            self.clients.remove(joining_client)
            self.selector.unregister(joining_client)

        data = common.safe_recv(joining_client, failure_callback)
        if not data:
            return

        (commands_for_joining, commands_for_rest) = (
            self.vim_state.get_vim_commands(data))

        joining_client.send(commands_for_joining)
        for client in self.clients:
            if client == joining_client:
                continue

            client.send(commands_for_rest)


def spawn(port):
    if os.fork() > 0:
        return
    os.chdir("/")
    os.setsid()
    os.umask(0)
    if os.fork() > 0:
        sys.exit(0)

    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()

    os.execl(__file__, str(port))


def main():
    common.setup_logging(is_leader=True)

    port = common.get_port()
    selector = selectors.DefaultSelector()

    leader = Leader(port, selector)
    try:
        leader.run()
    except Exception as e:
        # The server is already active.
        return

    while True:
        if not leader.clients and leader.had_clients:
            break
        for key, mask in selector.select():
            callback = key.data
            callback(key.fileobj)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception("Uncaught error: %r" % e)
