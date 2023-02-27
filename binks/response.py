# coding=utf-8

from binks.request import Request
from binks.utils import logger

class Response(object):
    def __init__(self, response_list, request):
        self.response_list = response_list
        self.response_headers = request.response_headers or {}
        self.status = request.response_status

    @property
    def buffers(self):
        resp_list = list()
        resp_list.append('HTTP/1.1 200 OK\r\n')
        resp_list.append('Server: Binks\r\n')
        resp_list.append('Connection: close\r\n')

        for head in self.response_headers:
            resp = '%s: %s\r\n' % (head[0], head[1])
            resp_list.append(resp)
        resp_list.append('\r\n')

        for body in self.response_list:
            resp_list.append(body)
        logger.debug('\n' + ''.join(resp_list))
        return ''.join(resp_list)