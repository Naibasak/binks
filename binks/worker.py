# coding=utf-8

import os
import io
import sys
import errno
import signal
import socket

try:
    import threading
except ImportError:
    import dummy_threading as threading

from binks.utils import logger,SIGNALS
from binks.loop import (
    BaseLoop,
    EventLoop,
    MODE_IN,
    MODE_OUT
)
from binks.request import Request
from binks.response import Response

import platform

BUF_SIZE = 4096


class Client(object):
    def __init__(self, sock, loop=None, app=None):
        self._socket = sock
        self.fd = sock.fileno()
        self.loop = loop
        self.app = app
        self.request = None
        self.response = None
        self._socket.setblocking(False)

    def read_callback(self):
        cache = b''
        try:
            while True:
                cache += self._socket.recv(BUF_SIZE)
        except socket.timeout as et:
            logger.info('read error %r', et)
        except socket.error as e:
            logger.info('read error %r', e)

        # print("buf ==", cache)
        # print("len ==", len(cache))

        self.handle_request(cache)
        self.loop.remove_callback(self.fd, MODE_IN, self.read_callback)

    def write(self):
        self.loop.add_callback(self.fd, MODE_OUT, self.write_callback)

    def write_callback(self):
        # logger.debug('write fd: %s, pid: %s', self.fd, os.getpid())
        buffers = self.response.buffers

        while len(buffers) > 0:
            try:
                lbytes = self._socket.send(buffers)
                if lbytes < len(buffers):
                    buffers = buffers[lbytes:]
                    continue
                break
            except socket.timeout as et:
                logger.info('write error %r', et)
            except socket.error as e:
                logger.info('write error %r', e)

        self.loop.remove_callback(self.fd, MODE_OUT, self.write_callback)
        self._socket.close()

    def process_request_thread(self, data):
        self.request = Request(data)
        response_list = self.app(self.request.environs, self.request.start_response)

        self.response = Response(response_list, request=self.request)
        self.write()


    def handle_request(self, data):
        """Start a new thread to process the request."""
        t = threading.Thread(target = self.process_request_thread,
                             args = (data,))
        t.daemon = False
        t.start()

    def __repr__(self):
        return '<Client fd:%s>' % self.fd


class Worker(object):
    def __init__(self, sock, app=None):
        self._socket = sock
        self.app = app
        self.loop = EventLoop()
        if platform.system() != "Windows":
            self.register_signals()

    def register_signals(self):
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)

    def handle_exit(self, signum, frame):
        pid = os.getpid()
        logger.info('Worker %s receive %s, exit...', pid, SIGNALS[signum])
        sys.exit(0)

    def accept_callback(self):
        try:
            client_socket, addr = self._socket.accept()
            # logger.debug('client socket: %s %s', client_socket.fileno(), addr)
            client = Client(client_socket, loop=self.loop, app=self.app)
            self.loop.add_callback(client.fd, MODE_IN, client.read_callback)
        except IOError  as e:
            if e.errno == errno.EWOULDBLOCK:
                pass
        except io.BlockingIOError as e:
            logger.debug('blocking error %s', e)

    def run(self):
        self.loop.add_callback(self._socket.fileno(), MODE_IN, self.accept_callback)
        try:
            self.loop.run()
        except SystemExit:
            logger.debug('SystemExit')
            return
        except Exception:
            logger.debug('Exception')
            raise
