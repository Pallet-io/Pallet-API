from .base import *

DEBUG = True

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