# coding=utf-8

class UrlRoutingMiddleware:
    apis = dict()

    def route(self, uri_path):
        def decorator_route(func):
            self.apis[uri_path] = func

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        return decorator_route

    @staticmethod
    def _execute_exc(environ):
        uri_path = environ['PATH_INFO']
        return 404,('%s not found' % uri_path).encode('utf-8')

    # def __call__(self, environ, start_response):
    #     path = environ['PATH_INFO']
    #     if self.apis.has_key(path):
    #         api = self.apis.get(path)
    #     else:
    #         api = _execute_exc
    #     return api(environ, start_response)

    def callRoute(self, uri_path, environ):
        if self.apis.has_key(uri_path):
            api = self.apis.get(uri_path)
        else:
            api = self._execute_exc
        return api(environ)

mw = UrlRoutingMiddleware()