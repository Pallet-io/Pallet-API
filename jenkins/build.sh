#!/bin/bash

# Description: build script for Jenkins CI.
#
# This script should be run in the project root.

sh setup_venv.sh
source env/bin/activate
pip install -r jenkins/requirements.txt

python oss_server/manage.py jenkins \
    --enable-coverage \
    --output-dir=jenkins/reports \
    --settings=oss_server.settings.jenkins
