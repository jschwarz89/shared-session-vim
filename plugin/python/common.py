import logging
import os
import time
import sys

LOGGING_PATH = "/tmp/ssvim"
DEFAULT_PORT = 1337

logger = logging.getLogger('ssvim')


def get_port():
    try:
        return int(sys.argv[1])
    except IndexError:
        return DEFAULT_PORT


def setup_logging(is_leader=False):
    if not os.path.exists(LOGGING_PATH):
        os.mkdir(LOGGING_PATH)

    base_filename = "ssvim"
    if is_leader:
        base_filename = "ssvim.leader"
    base_filename = "%s.%s.log" % (base_filename,
                               time.strftime("%Y%m%d.%H%M%S"))

    path = os.path.join(LOGGING_PATH, base_filename)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    logger.setLevel(logging.DEBUG)
    for handler in [logging.FileHandler(path)]:  # , logging.StreamHandler()]:
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def safe_recv(socket, failure_callback):
    data = socket.recv(4096)
    if not data:
        return failure_callback()

    result = data.decode()
    while True:
        try:
            data = socket.recv(4096)
        except BlockingIOError:
            # No more data to read
            break
        result += data.decode()

    logger.debug("Received command from socket: %s" % result)
    return result
