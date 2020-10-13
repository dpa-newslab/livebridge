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

.. note::
    It is recommended, to install Livebridge in a dedicated Virtualenv_ Python environment!

Settings
--------

:ref:`The specific bridges will be specified in an extra .yaml control file or in a database table! <control>`

Some global settings are defined in `livebridge/config.py`_. These values can be set through **environment variables**.  Following variables for configuration are available:

* **LB_CONTROLFILE** - path to control file, overrides **--control** commandline argument.
* **LB_LOGLEVEL** - Python logging level, *INFO* is default, can be *DEBUG, INFO, WARNING, ERROR* or *CRITICAL*
* **LB_LOGFILE** - path to write a logfile, *optional*
* **LB_POLL_INTERVAL** - interval in seconds for polling an API for new posts when using a polling-source, defaults to **60** seconds.
  **Please be attentitive how often you are polling your source. Liveticker have other constraints like RSS Feeds!**
* **LB_POLL_CONTROL_INTERVAL** - interval in seconds for polling for control data changes, defaults to **60** seconds.
  *This does not apply to local control files. If not configured otherwise, a restart is neccessary after changes to local control files.*
* **LB_CONTROLFILE_WATCH** - setting to **true** will force checks on local control files for changed control data.
* **LB_MAX_RETRIES** - number of maximal retries for redistributing a failed item, defaults to **10**.
* **LB_RETRY_MULTIPLIER** - delay multiplier for retrying a failed distribution, defaults to **5** seconds. Retry delay is calclulated by multiplicating **LB_RETRY_MULTIPLIER** with the **number of the last retry**.

To use MongoDB_ or any **SQL** database supported by SQLALchemy_ as storage backend, you have to specify the following two environment variables:

* **LB_DB_DSN** - dsn database url for connecting with a database, see docs for `SQLAlchemy engines`_ or `MongoDB connection strings`_ for details. To disable storage, set this env-var to **dummy://**.
* **LB_DB_TABLE** - name of the database table which stores distribution related data, defaults to **livebridge_dev**.
* **LB_DB_CONTROL_TABLE** - name of the database table, which stores control data in JSON format, overrides **--control**.

 **Be sure the database already exists and the database user from the dsn-url string has sufficient rights.**

.. note::
    For simple, straight forward distribution, storage can be disabled by setting **LB_DB_DSN=dummy://**. Updates and deletes of distributed posts will therefore be not applied.

Since livebridge also supports `AWS DynamoDB`_ as storage backend, following **Amazon AWS** related config variables are available:

* **LB_AWS_ACCESS_KEY** - AWS access key
* **LB_AWS_SECRET_KEY** - AWS secret access key
* **LB_AWS_REGION** - defaults to **eu-central-1**
* **LB_DYNAMO_ENDPOINT**  - Endpoint url for DynamoDB. Can be empty, except when using a local DynamoDB.
* **LB_DYNAMO_TABLE** - Tablename, defaults to **livebridge-posts**.
* **LB_DYNAMO_CONTROL_TABLE** - name of the DynamoDB table, which stores control data in JSON format, overrides **--control**.
* **LB_SQS_S3_QUEUE** - SQS-QueueUrl for listening for control file changes on S3.

 **The DynamoDB tables will be automatically created, if defined and they're not existing. Sufficient** `AWS IAM`_ **rights are required.**

.. _webapisettings:

For using the :ref:`Web-API <webapi>` following settings have to be set:

* **LB_WEB_HOST** - the host the server is listening on. *0.0.0.0* or *127.0.0.1* for example.
* **LB_WEB_PORT** - the port the server is listening on, *8080* for example.
* **LB_WEB_USER** - Username of the API user. *Only a single user supported at the moment!*
* **LB_WEB_PWD** - Password of the API user.

See :ref:`Web-API <webapi>` for more details.

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
