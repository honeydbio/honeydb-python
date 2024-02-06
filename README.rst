HoneyDB
==================

.. image:: https://img.shields.io/pypi/v/honeydb.svg
    :target: https://pypi.python.org/pypi/honeydb/
    :alt: Latest Version

To learn more about HoneyDB visit `About HoneyDB`_.

To lean more about the HoneyDB API visit `HoneyDB REST API`_.

The ``honeydb`` command is a CLI tool for interacting with the HoneyDB API. 

Installation
------------
.. code-block:: bash

    $ pip install honeydb


CLI usage
---------
.. code-block:: bash

    $ export HONEYDB_API_ID=<your api id>
    $ export HONEYDB_API_KEY=<your api key>
    $ honeydb --bad-hosts


Module usage
------------
.. code-block:: python

    from honeydb import api
    honeydb = api.Client('api_id', 'api_key')
    print(honeydb.bad_hosts())

More details and the latest updates can be found on the `GitHub Project Page`_.

.. _About HoneyDB: https://honeydb.io/#about
.. _HoneyDB REST API: https://honeydb.io/#threats
.. _GitHub Project Page: https://github.com/honeydbio/honeydb-python
