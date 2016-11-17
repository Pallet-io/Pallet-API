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
### database
OSS explorer module uses mysql to store blockchain data. Make sure to create a
database named `explorer_db` beforehand and fill in `USER` and `PASSWORD` in the
`DATABASES` setting, then migrate with:

    ./manage.py migrate --database explorer_db

## Run server
### Activate virtualenv
    source env/bin/activate
### Start server
    ./oss_server/manage.py runserver <address>:<port>

## Sync explorer with blockchain
Before explorer can sync with blockchain data, you have to tell explorer the
location of blockchain data, which are usually located under `~/.gcoin/main/blocks`.

Open `explorer/configs.py` and set `BLK_DIR` to the directory holding blockchain data.

Run `./manage.py blockupdate` to sync blockchain indefinitely.
