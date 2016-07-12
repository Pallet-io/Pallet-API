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
