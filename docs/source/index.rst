.. _index:

Livebridge
==========

by dpa•newslab

.. image:: https://travis-ci.org/dpa-newslab/livebridge.svg?branch=master
    :target: https://travis-ci.org/dpa-newslab/livebridge
.. image:: https://coveralls.io/repos/github/dpa-newslab/livebridge/badge.svg?branch=master
    :target: https://coveralls.io/github/dpa-newslab/livebridge?branch=master
.. image:: https://badge.fury.io/py/livebridge.svg
    :target: https://pypi.python.org/pypi/livebridge

Millions of users read `dpa-Live <https://www.dpa.com/de/produkte-services/liveticker-newsblogs/#liveticker>`_ updates when a new US president is elected or an ongoing attack of unknown origin keeps the nation awake.  We strive to deliver these updates live to whatever publishing system our customers chose. So we developed this open-source software as part of a project funded by the `Google DNI Fund <https://www.digitalnewsinitiative.com/>`_.

We’re already using it in production, delivering content produced using `Sourcefabric’s Liveblog <https://github.com/liveblog/liveblog>`_  in the dpa newsroom to media customers who use the service of `ScribbleLive <http://scribblelive.com>`_.


.. note::
    Livebridge requires Python >= 3.5


Features
--------

* Keep content in-sync over different services.
* syndicate one source to various targets in realtime.
* CRUD - create, update, delete of resources over different services.
* extensible for all kinds of services with plugins
* Web-UI for controlling running bridges through a convenient web-frontend.
* Web-API for controlling running bridges.
* running bridges can be controlled without restarting the process.
* supported storage backends: MongoDB, DynamoDB, MySQL, PostgreSQL, MSSQL, Oracle and others
* no storage backend needed for simple forwarding distribution of posts.
* await/async based, Python 3.5
* (non-persistent) queues for retrying the distribution of a post.
* focus on robustness and stability



Available Plugins
-----------------

.. include:: plugins.rst
   :start-line: 4
   :end-line: 13


Installation & Setup
--------------------

.. toctree::
   :maxdepth: 2

   quickstart
   control
   webapi
   extras
   developing
   tutorial

Plugins
-------

.. toctree::
   :maxdepth: 2

   plugins
   ownplugins
   pluginapi

License
-------

**Apache License, Version 2.0 - see** LICENSE_ **for details.**

.. include:: links.rst
