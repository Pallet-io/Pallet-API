# OSS
A REST api for gcoin rpc.

## Installation
### Requirement
- Python 2.7
- virtualenv

### Setup
    ./setup_venv.sh
    
## Configuration
### gcoin rpc
Set up gcoin rpc in file `oss_server/oss_server/settings/base.py`.

    GCOIN_RPC = {
        'user': '<user>',
        'password': '<passwrod>',
        'host': '<host>',
        'port': '<port>',
    }

## Run server
### Activate virtualenv
    source env/bin/activate
### Start server
    ./oss_server/manage.py runserver <address>:<port>
