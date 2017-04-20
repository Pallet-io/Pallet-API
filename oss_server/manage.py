#!/usr/bin/env python
import os
import sys
from oss_server.settings.base import SERVER_CONFIG_ENV

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SERVER_CONFIG_ENV)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
