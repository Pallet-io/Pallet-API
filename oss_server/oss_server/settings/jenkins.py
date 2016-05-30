from .base import *

INSTALLED_APPS += (
    'base',
    'django_jenkins',
)

PROJECT_APPS = (
    'base',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_flake8',
    'django_jenkins.tasks.run_pylint',
)
