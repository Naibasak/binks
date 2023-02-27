# coding=utf-8
from binks.utils import logger

def app(environ, start_response):
    """Simplest possible application object"""
    data = b'Hello,World Binks\n'
    status = '200 OK'
    response_headers = [
        ('Content-type','application/json'),
        ('Content-Length', len(data))
    ]

    logger.debug('environ:%s', environ)

    start_response(status, response_headers)
    return [data]
