.. _webapi:

Web-API
=======

Livebridge provides a simple Web-API endpoint for retrieving and/or saving of :ref:`control data, as described here <control>`.

For using the :ref:`Web-API <webapi>` following settings have to be set:

* **LB_WEB_HOST** - the host the server is listening on. *0.0.0.0* or *127.0.0.1* for example.
* **LB_WEB_PORT** - the port the server is listening on, *8080* for example.
* **LB_WEB_USER** - Username of the API user. *Only a single user supported at the moment!*
* **LB_WEB_PWD** - Password of the API user.

For more details about Web-API related configuration values, see :ref:`here <webapisettings>`.


Endpoint
--------

.. code-block:: bash

    #scheme
    https://[LB_WEB_HOST]:[LB_WEB_PORT]/api/v1/

    # example
    https://localhost:8080/api/v1/

Authentication
--------------

All requests require a HTTP-Header **X-Auth-Token** for authentication requests.


.. code-block:: bash

  POST /api/v1/session

To retrieve this token for subsequent requests, **/api/v1/session** can be called, 
with the credentials defined in **LB_WEB_USER** and **LB_WEB_PWD**.

.. code-block:: bash

    $ curl -XPOST -s -d "username=yourusername&password=yourpassword" \
    http://localhost:8080/api/v1/session

The response returns a **HTTP status 200** contains a JSON document with the token included:

.. code-block:: bash

    {"token": "58725ad5-d669-4431-9991-1a0cff261526"}

This token is stored in memory by the API and will get invalid at restart and after re-requesting a new token.

Control bridges
---------------

.. code-block:: bash

  [GET/PUT] /api/v1/controldata

This resource allows to retrieve and edit the :ref:`controlling of livebridges <control>`. The data handled is :ref:`JSON-formatted <controljson>`, independent from the used storage backend (file, s3, DBs).

**Retrieving current control data**

To get the current active control-data, a **GET** request on the resource returns the control data in JSON format, no parameters are required:

.. code-block:: bash

    curl -XGET -s -H "X-Auth-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    http://localhost:8080/api/v1/controldata

A successful request returns data with a **HTTP status 200**:

.. code-block:: bash

    {
        "auth": {
            "live": {
                "user": "prod",
                "password": "pwd2",
                "api_key": "Foobar"
            }
        },
        "bridges": [{
            "endpoint": "https://example.com/api/",
            "label": "Example 1",
            "source_id": "abcdefg",
            "targets": [{
                "type": "another",
                "event_id": "654321",
                "auth": "live"
            }]
        }]
    }


**Putting new control data**

With a **PUT** operation, initial control data can be saved or existing control data can be updated.

The request-payload is :ref:`JSON-formatted <controljson>` and uploaded as request-body:

.. code-block:: bash

    curl -XPUT -v -H "X-Auth-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -T control-api.json \
    http://localhost:8080/api/v1/controldata

A successful **PUT** operation returns with a **HTTP status 200** following:

.. code-block:: bash

    {"ok": "true"}

If no control data exists, one can store initial control data this way.

.. note::
    Running bridges are not restarted promptly after control data was updated. Instead the next
    periodically check for changed control data is awaited. The interval for these checks are
    defined by **LB_POLL_CONTROL_INTERVAL**.

Error responses
---------------

Error responses have the general, JSON-formatted form:

.. code-block:: bash

    {"error": "Message"}

Following errors are possible:

+-------------+-------------------------------+
|     HTTP    | Error                         |
+=============+===============================+
|     400     | Auth credentials are missing. |
+-------------+-------------------------------+
|     400     | Controldata was not saved.    |
+-------------+-------------------------------+
|     400     | No request body was found.    |
+-------------+-------------------------------+
|     401     | Not authorized.               |
+-------------+-------------------------------+
|     401     | Invalid token.                |
+-------------+-------------------------------+
|     401     | Method Not Allowed            |
+-------------+-------------------------------+
|     500     | Internal Server Error         |
+-------------+-------------------------------+
