# honeydb-python

[![Format & Lint](https://github.com/honeydbio/honeydb-python/actions/workflows/format-lint.yml/badge.svg)](https://github.com/honeydbio/honeydb-python/actions/workflows/format-lint.yml)

HoneyDB Python Module

### Install

`pip install honeydb`

### CLI Usage

```
$ export HONEYDB_API_ID=<your api id>
$ export HONEYDB_API_KEY=<your api key>
$ honeydb --bad-hosts
```

Display help message for more CLI options:

`honeydb --help`

### Module Usage

```
from honeydb import api
honeydb = api.Client('api_id', 'api_key')
print(honeydb.bad_hosts())
```
