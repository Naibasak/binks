# coding=utf-8

import sys
import signal
import logging
import importlib

logger = logging.getLogger('Binks')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] pid: %(process)d %(levelname)s:%(filename)s:%(lineno)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


import platform
if platform.system() == "Windows":
    SIGNALS = {}
else:
    SIGNALS = {
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM',
        signal.SIGQUIT: 'SIGQUIT',
        signal.SIGCHLD: 'SIGCHLD',
        signal.SIGUSR1: 'SIGUSR1'
    }

def import_app(module):
    module_name, app_name = module.rsplit(':')
    module = importlib.import_module(module_name)
    try:
        obj = getattr(module, app_name)
    except AttributeError:
        raise ImportError('Failed to find application object: %s.', app_name)
    if not callable(obj):
        raise TypeError('Application object must be callable.')
    return obj
