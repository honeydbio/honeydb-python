HoneyDB
==================

``honeydb`` is a Python wrapper for the `HoneyDB REST API`_.

Installation
------------
.. code-block:: bash

    $ pip install honeydb


CLI usage
---------
.. code-block:: bash

    $ honeydb --bad-hosts


Module usage
------------
.. code-block:: python

    from honeydb import api
    honeydb = api.Client('api_id', 'api_key')
    print(honeydb.bad-hosts())

More details and the latest updates can be found on the `GitHub Project Page`_.

.. _HoneyDB REST API: https://riskdiscovery.com/honeydb/#threats
.. _GitHub Project Page: https://github.com/foospidy/honeydb-python