# coding=utf-8
from binks.utils import logger
from binks.UrlRoutingMiddleware import mw

@mw.route('/hello')
def hello(environ):
    return 200, "hello world!"

def app(environ, start_response):
    """Simplest possible application object"""
    # logger.debug('environ:%s', environ)

    path = environ['PATH_INFO']
    status, data = mw.callRoute(path, environ)
    response_headers = [
        ('Content-type','application/json'),
        ('Content-Length', len(data))
    ]

    start_response(status, response_headers)
    return [data]
