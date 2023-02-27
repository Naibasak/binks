# coding=utf -8

import select
import errno
import platform
from collections import defaultdict

from binks.utils import logger

MODE_NULL = 0x00
MODE_IN = 0x01
MODE_OUT = 0x04
MODE_ERR = 0x08
MODE_HUP = 0x10
MODE_NVAL = 0x20


class BaseLoop(object):
    def __init__(self):
        self._fds_to_handlers = defaultdict(list)

    def poll(self, timeout):
        raise NotImplementedError()

    def register(self, fd, mode):
        raise NotImplementedError()

    def unregister(self, fd):
        raise NotImplementedError()

    def modify(self, fd, mode):
        raise NotImplementedError()

    def add_callback(self, fd, mode, callback):
        handlers = self._fds_to_handlers[fd]
        handlers.append((mode, callback))
        self.register(fd, mode)

    def remove_callback(self, fd, mode, callback):
        handlers = self._fds_to_handlers[fd]
        handlers.remove((mode, callback))
        if len(handlers) == 0:
            # logger.debug('remove fd: %d', fd)
            self.unregister(fd)

    def run(self):
        try:
            while True:
                fds_ready = self.poll(1)
                for fd, mode in fds_ready:
                    # logger.debug('fds_ready: %d, mode:%d', fd, mode)
                    handlers = self._fds_to_handlers[fd]
                    for m, callback in handlers:
                        if m & mode != 0:
                            callback()
        except (OSError, select.error) as e:
            if e.args[0] != errno.EINTR:
                raise
        # except KeyboardInterrupt as ek:
        #     logger.debug('KeyboardInterrupt ...')
        #     if platform.system() == "Windows":
        #         exit(0)

class SelectLoop(BaseLoop):
    def __init__(self):
        super(SelectLoop, self).__init__()
        self._r_list = set()
        self._w_list = set()
        self._e_list = set()

    def poll(self, timeout):
        r, w, e = select.select(self._r_list, self._w_list, self._e_list, timeout)
        results = defaultdict(lambda: MODE_NULL)
        for fds, mode in [(r, MODE_IN), (w, MODE_OUT), (e, MODE_ERR)]:
            for fd in fds:
                results[fd] |= mode
        return results.items()

    def register(self, fd, mode):
        if mode & MODE_IN:
            self._r_list.add(fd)
        if mode & MODE_OUT:
            self._w_list.add(fd)
        if mode & MODE_ERR:
            self._e_list.add(fd)

    def unregister(self, fd):
        if fd in self._r_list:
            self._r_list.remove(fd)
        if fd in self._w_list:
            self._w_list.remove(fd)
        if fd in self._e_list:
            self._e_list.remove(fd)

    def modify(self, fd, mode):
        self.unregister(fd)
        self.register(fd, mode)


class EpollLoop(BaseLoop):
    def __init__(self):
        super(EpollLoop, self).__init__()
        if hasattr(select, 'epoll'):
            self._epoll = select.epoll()
        else:
            raise AttributeError('module "select" has no attribute "epoll"')

    def poll(self, timeout):
        return self._epoll.poll(timeout)

    def register(self, fd, mode):
        try:
            self._epoll.register(fd, mode | select.EPOLLET)
        except IOError as e:
            if e.errno == errno.EEXIST:
                self.modify(fd, mode)

    def unregister(self, fd):
        self._epoll.unregister(fd)

    def modify(self, fd, mode):
        self._epoll.modify(fd, mode | select.EPOLLET)


if hasattr(select, 'epoll'):
    EventLoop = EpollLoop
else:
    EventLoop = SelectLoop
