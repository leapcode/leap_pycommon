leap.common
===========

.. image:: https://badge.fury.io/py/leap.common.svg
    :target: http://badge.fury.io/py/leap.common
.. image:: https://img.shields.io/pypi/dm/leap.common.svg
    :target: http://badge.fury.io/py/leap.common

A collection of shared utils used by the several python LEAP subprojects.

* leap.common.cert
* leap.common.checks
* leap.common.config
* leap.common.events
* leap.common.files
* leap.common.testing

Library dependencies
--------------------
* ``libssl-dev``

Python dependencies
-------------------
* See ``pkg/requirements.pip``

Extras
-------------------
Using `leap.common.http` needs some extra dependencies (twisted.web >= 14.0.2,
python-service-identity). You can install them by running::

  pip install leap.common[http]


Running the tests
-------------------
To run the tests, first run the setup with:

.. code-block::
pip install -r pkg/requirements.pip
pip install -r pkg/requirements-testing.pip

After that you can run the tests with

.. code-block::
trial leap.common
