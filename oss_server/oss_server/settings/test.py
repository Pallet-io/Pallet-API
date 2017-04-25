from .base import *

DEBUG = True

SERVER_CONFIG_ENV = 'oss_server.settings.' + 'test'

INSTALLED_APPS += [
    'base',
    'explorer',
    'notification',
]

SOUTH_TESTS_MIGRATE = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}