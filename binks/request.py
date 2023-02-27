# coding=utf-8

import werkzeug_raw
from binks.utils import logger

class Request(object):
    def __init__(self, buffers):
        self._buffers = buffers
        self.response_status = ''
        self.response_headers = {}

    @property
    def environs(self):
        logger.debug('\n' + self._buffers)
        return werkzeug_raw.environ(self._buffers)

    def start_response(self, status, response_headers):
        self.response_status = status
        self.response_headers = response_headers or {}
