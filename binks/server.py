# coding=utf-8

import os
import sys
import time
import errno
import signal
import socket

from binks.worker import Worker
from binks.utils import logger,SIGNALS

import platform

class Server(object):
    def __init__(self, address, app=None, worker_num=5):
        self.workers_pid = []
        self._address = address
        self.app = app
        self.worker_num = worker_num
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_sockopts()
        self._socket.bind(address)

    def listen(self, backlog = 128):
        self._socket.listen(backlog)
        logger.info('Listening %s ...', str(self._address))

    def set_sockopts(self):
        self._socket.setblocking(False)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if platform.system() != "Windows":
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def register_signals(self):
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)

    def handle_exit(self, signum, frame):
        logger.info('Server receive %s', SIGNALS[signum])
        self.stop()

    def run(self):
        if platform.system() == "Windows":
            self.run_windows()
        else:
            self.listen()
            self.spawn_workers()

    def run_windows(self):
        self.listen()
        worker = Worker(self._socket, app=self.app)
        worker.run()


    def stop(self):
        signum = signal.SIGTERM
        for pid in self.workers_pid:
            self.kill_worker(pid, signum)
        del self.workers_pid
        logger.info('Server is shutting down...')

    def kill_worker(self, pid, signum):
        while True:
            try:
                os.kill(pid, signum)
                pid, stat = os.waitpid(pid, 0)
                if pid:
                    logger.info('Worker %s has been killed', pid)
                    break
            except OSError as e:
                if e.errno == errno.ECHILD:
                    break
                elif e.errno == errno.EINTR:
                    continue
                else:
                    raise

    def reap_workers(self):
        while True:
            try:
                pid, stat = os.waitpid(-1, os.WNOHANG)
                if not pid:
                    break
                self.workers_pid.remove(pid)
            except OSError as e:
                if e.errno == errno.ECHILD:
                    pass

    def spawn_workers(self):
        p = 0
        for i in range(self.worker_num):
            p = 0
            pid = os.fork()
            if pid == 0:
                break
            elif pid > 0:
                p = pid
                self.workers_pid.append(pid)
            else:
                pass

        if p == 0:
            try:
                worker = Worker(self._socket, app=self.app)
                worker.run()
            except Exception:
                raise
        else:
            self.register_signals()
            try:
                while True:
                    self.reap_workers()
                    time.sleep(4)
            except KeyboardInterrupt:
                logger.info('Receive SIGINT...')
                self.stop()
            sys.exit(0)
