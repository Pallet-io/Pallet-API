# Pallium API
A REST api for bitcoin rpc. Copyright (c) 2017-2018 Pallium Open Source Community.

## Installation
### Requirement
- Python 2.7
- virtualenv

### Setup
    ./setup_venv.sh
## Configuration
### Set up setting.py

```
cp oss_server/oss_server/settings/setting.py.default oss_server/oss_server/settings/setting.py
```

### Modify setting.py

#### Secret key

`<SECRET_KEY>`

This is used to provide cryptographic signing, and should be set to a unique, unpredictable value.

#### Environment

`<ENV>`

Fill in `develop` will enable `oss_server/oss_server/settings/develop.py` for debug information while running the project.

`test`: `oss_server/oss_server/settings/test.py`

It is designed for a standalone unit test process using a in-memory database.

`production`: `oss_server/oss_server/settings/production.py`

It disable debug information for production environment.

#### Allowed hosts

`<ALLOW_DOMAIN>`

Replacing it with `*` means it allowed requests from everywhere.

Use `*` for develop and subdomain format for production environment.

#### Bitcoin rpc

Set up connection of bitcoin rpc

```
BITCOIN_RPC = {
    'user': '<BITCOIN_RPC_USER>',
    'password': '<BITCOIN_RPC_PASSWORD>',
    'host': '<BITCOIN_RPC_HOST>',
    'port': '<BITCOIN_RPC_PORT>',
}
```
#### Database
OSS uses mariadb to store blockchain data. Make sure to create a database named the same as `<EXPLORER_DB_NAME>`, then migrate with:

`./manage.py migrate`

```
DATABASES = {
    'default': {
        'NAME': '<EXPLORER_DB_NAME>',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '<EXPLORER_DB_HOST>',
        'PORT': '<EXPLORER_DB_PORT>',
        'USER': '<EXPLORER_DB_USER>',
        'PASSWORD': '<EXPLORER_DB_PSSWORD>',
        'CONN_MAX_AGE': 20
    }
}
```

#### Sync database with blockchain

`<NET>`

Set `MAINNET` to update blocks of bitcoin mainnet and `TESTNET` for testnet.

`<BTC_DIR>`

The data forlder, which are usually located under `~/.bitcoin`

It is the key point for entire OSS project. The Django command called `blockupdate` will read all the blockchain data under this forlder every second by default and save these data to specified database.

Run `./manage.py blockupdate` to sync blockchain indefinitely.

## Run unit test

Run `./manage.py test --settings=oss_server.settings.test` for a standalone unit test.

Run `./manage.py test` will create a test database specified in setting.py and destroy it after compeleting the test.

## Run server

### Start server
    ./oss_server/manage.py runserver <address>:<port>

### Start services

	./manage.py blockupdate
	./manage.py txnotify
	./manage.py addressnotify
