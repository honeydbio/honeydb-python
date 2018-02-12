==================
HoneyDB
==================

``honeydb`` is a Python wrapper for the `HoneyDB REST API`_.

-----
usage
-----
::

    from honeydb import api
    honeydb = api.Client('api_id', 'api_key')
    honeydb.bad-hosts()

More details and the latest updates can be found on the `GitHub Project Page`_.

.. _HoneyDB REST API: https://riskdiscovery.com/honeydb/#threats
.. _GitHub Project Page: https://github.com/foospidy/honeydb-python