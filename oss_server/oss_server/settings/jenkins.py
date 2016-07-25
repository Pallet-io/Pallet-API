from .base import *

INSTALLED_APPS += (
    'base',
    'explorer',
    'django_jenkins',
)

PROJECT_APPS = (
    'base',
    'explorer',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_flake8',
    'django_jenkins.tasks.run_pylint',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'explorer_db': {
        'NAME': 'explorer_db',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'root',
        'PASSWORD': ''
    }
}
