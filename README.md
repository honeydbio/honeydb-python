# honeydb-python

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
