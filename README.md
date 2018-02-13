# honeydb-python

[![Build Status](https://travis-ci.org/foospidy/honeydb-python.svg?branch=master)](https://travis-ci.org/foospidy/honeydb-python)

HoneyDB Python Module

### Install

`pip install honeydb`

### CLI Usage

Display help message for CLI options:

`honeydb --help`

### Module Usage

```
from honeydb import api
honeydb = api.Client('api_id', 'api_key')
print(honeydb.bad-hosts())
```
