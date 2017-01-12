.. _quickstart:

Quick start guide
=================


Installation
------------
    
A **Python** version **>=3.5** is required to install **livebridge**, since it is based and makes heavy use of Asyncio_, an event loop introduced by Python3.

.. code-block:: bash

    pip3 install livebridge

A **livebridge** command will be available afterwards.

.. code-block:: bash

    $ livebridge 
    usage: livebridge [-h] --control CONTROL
    livebridge: error: the following arguments are required: --control


Settings
--------

:ref:`The specific bridges will be specified in an extra .yaml control file! <control>`

Some global settings are defined in `livebridge/config.py`_. These values can be set through **environment variables**.  Following variables for configuration are available:

* **LB_CONTROLFILE** - path to control file, overrides **--control** commandline argument.
* **LB_LOGLEVEL** - Python logging level, *INFO* is default, can be *DEBUG, INFO, WARNING, ERROR* or *CRITICAL*
* **LB_LOGFILE** - path to write a logfile, *optional*
* **LB_POLL_INTERVAL** - interval in seconds for polling an API for new posts when using a polling-source, defaults to 60 seconds. 
  **Please be attentitive how often you are polling your source. Liveticker have other constraints like RSS_Feeds!**

To use any **SQL** database supported by SQLALchemy_ as storage backend, you have to specify the following two environment variables:

* **LB_DB_DSN** - dsn database url for connecting with a database, see http://docs.sqlalchemy.org/en/latest/core/engines.html for details.
* **LB_DB_TABLE** - name of the database table, that will be created, defaults to **livebridge_dev**. Be sure the database already exists and the database user from the **dsn-url** string has sufficient rights.

Since livebridge also supports `AWS DynamoDB`_ as storage backend, following **Amazon AWS** related config variables are available:

* **LB_AWS_ACCESS_KEY**
* **LB_AWS_SECRET_KEY**
* **LB_AWS_REGION** - defaults to **eu-central-1**
* **LB_DYNAMO_ENDPOINT**  - Endpoint url for DynamoDB. Can be empty, except when using a local DynamoDB.
* **LB_DYNAMO_TABLE** - Tablename, defaults to **livebridge_posts**. The DynamoDB table will be automatically created, if it not exists. *Sufficient* `AWS IAM`_ *rights are required.*
* **LB_SQS_S3_QUEUE** - SQS-QueueUrl for listening for control file changes on S3.


Testing
-------

**Livebridge** uses `pytest`_ and `asynctest`_ for testing.

Run tests:

.. code-block:: bash

    py.test -v tests/

Run tests with test coverage:

.. code-block:: bash

    py.test -v --cov=livebridge --cov-report=html tests/

`pytest-cov`_ has to be installed. In the example above, a html summary of the test coverage is saved in **./htmlcov/**.

.. include:: links.rst
