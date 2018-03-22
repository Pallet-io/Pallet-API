#!/bin/bash
#
# setup_venv.sh is a script to create a virtual environment.
# it will create a virtual environment in env directory and
# install all packages listed in requirements.txt and packages
# directory.
#
# Usage:
#     ./setup_venv.sh
#

# check whether virtualenv is installed
command -v virtualenv > /dev/null 2>&1 || { echo >&2 "virtualenv is not installed. Aborting."; exit 1;}

virtualenv -p python3 env
source env/bin/activate

pip3 install -r requirements.txt
