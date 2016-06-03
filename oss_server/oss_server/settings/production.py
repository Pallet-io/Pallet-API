from .base import *

DEBUG = False

# Logger

BASE_MODULE_LOG_FILE = '/tmp/log'

LOGGING = {
    'version': 1,
    'handlers': {
        'base_log_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_MODULE_LOG_FILE,
            'formatter': 'api_format'
        }
    },
    'formatters': {
        'api_format': {
            'format': '%(levelname)s %(asctime)s %(endpoint)s %(message)s'
        }
    },
    'loggers': {
        'base': {
            'handlers': ['base_log_file'],
            'level': 'INFO'
        }
    }
}
