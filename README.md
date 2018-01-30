# Livebridge by dpa-newslab

[![Build Status](https://travis-ci.org/dpa-newslab/livebridge.svg?branch=master)](https://travis-ci.org/dpa-newslab/livebridge)
[![Coverage Status](https://coveralls.io/repos/github/dpa-newslab/livebridge/badge.svg?branch=master)](https://coveralls.io/github/dpa-newslab/livebridge?branch=master)
[![PyPi](https://badge.fury.io/py/livebridge.svg)](https://pypi.python.org/pypi/livebridge)

Millions of users read [dpa-Live](https://www.dpa.com/de/produkte-services/liveticker-newsblogs/#liveticker) updates when a new US president is elected or an ongoing attack of unknown origin keeps the nation awake.  We strive to deliver these updates live to whatever publishing system our customers chose. So we developed this open-source software as part of a project funded by the [Google DNI Fund](https://www.digitalnewsinitiative.com/). Read [Introducing Live Coverage Ecosystem](https://blog.sourcefabric.org/en/news/blog/3434/Introducing-Live-Coverage-Ecosystem-funded-by-Google.htm) for more details.

We’re already using it in production, delivering content produced using [Sourcefabric’s Liveblog](https://github.com/liveblog/liveblog)  in the dpa newsroom to media customers who use the service of [ScribbleLive](http://scribblelive.com).

## Features

- Keep content in-sync over different services.
- syndicate one source to various targets in realtime.
- **CRUD** - create, update, delete of resources over different services.
- extensible for all kinds of services with [plugins](http://livebridge.readthedocs.io/en/stable/ownplugins.html)
- Web-UI for controlling running bridges through a convenient web-frontend.
- Web-API for controlling bridges.
- service credentials as environment vars.
- supported storage backends: MongoDB, DynamoDB, MySQL, PostgreSQL, MSSQL, Oracle and others
- [await/async](https://docs.python.org/3/library/asyncio.html) based, Python 3.5
- (non-persistent) queues for retrying the distribution of a post.
- focus on robustness and stability


## Installation 

```sh
pip3 install livebridge
```
**Python >=3.5 is required**. <br>
See http://livebridge.readthedocs.io/en/stable/quickstart.html#installation for details.

## Settings
Global settings are defined in [livebridge/config.py](livebridge/config.py). These values can be set through **environment variables**.  

See http://livebridge.readthedocs.io/en/stable/quickstart.html#settings for available configuration variables.

## Running
The **livebridge** command expects a **-control=** parameter (alternatively the environment vars *LB_CONTROLFILE** or **LB_DB_CONTROL_TABLE**), to specify the place of the control data with the configured bridges.  **--control** can be either a **local control file** or a **remote control file** on **s3**.

* with local control file
```sh
livebridge --control=/path/to/control.yaml
```
* with remote control file on S3
```sh
livebridge --control=s3://bucketname/control.yaml
```
* with control data stored in a database
```sh
... LB_DB_CONTROL_TABLE=lb_control livebridge
```

See http://livebridge.readthedocs.io/en/stable/control.html for more details.

## Documentation

http://livebridge.readthedocs.io/en/stable/

## Plugins
Several source and targets are available as **[plugins]( http://livebridge.readthedocs.io/en/stable/plugins.html)**. Following plugins are currently available:

* **[Liveblog](https://github.com/dpa-newslab/livebridge-liveblog)**  - Provides a Liveblog liveticker as source.
* **[Scribblelive](https://github.com/dpa-newslab/livebridge-scribblelive)**  - Provides a Scribblelive event stream as target.   Provides also a **converter** from **Liveblog** to **Scribblelive**.
* **[Slack](https://github.com/dpa-newslab/livebridge-slack)** - Provides Slack channels as source and as target. Also provides **converters** from **Liveblog** and to **Scribblelive**.
* **[Tickaroo](https://github.com/Tickaroo/livebridge-tickaroo)** - Provides a **Tickaroo** ticker as target.


It's possbile to write own service plugins and to make them available to **livebridge** as a Python module via *[PyPI](https://pypi.python.org/pypi)*.
See *https://github.com/dpa-newslab/livebridge-slack* as an example plugin.

**[Tutorial: How to build a Livebridge plugin](http://livebridge.readthedocs.io/en/stable/tutorial.html)**

## Developing

See http://livebridge.readthedocs.io/en/stable/developing.html


## Testing
**Livebridge** uses [py.test](http://pytest.org/) and [asynctest](http://asynctest.readthedocs.io/) for testing.

Run tests:

```sh
    py.test -v tests/
```

Run tests with test coverage:

```sh
    py.test -v --cov=livebridge --cov-report=html tests/
```

[pytest-cov](https://pypi.python.org/pypi/pytest-cov) has to be installed. In the example above, a html summary of the test coverage is saved in **./htmlcov/**.


## License
Copyright 2016-2018 dpa-infocom GmbH

Apache License, Version 2.0 - see LICENSE for details

