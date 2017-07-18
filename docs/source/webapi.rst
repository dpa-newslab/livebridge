.. _webapi:

Web-API
=======

Livebridge provides a simple Web-API endpoint for retrieving and/or saving of :ref:`control data, as described here <control>`.

For using the :ref:`Web-API <webapi>` following settings have to be set:

* **LB_WEB_HOST** - the host the server is listening on. *0.0.0.0* or *127.0.0.1* for example.
* **LB_WEB_PORT** - the port the server is listening on, *8080* for example.
* **LB_WEB_USER** - Username of the API user. *Only a single user supported at the moment!*
* **LB_WEB_PWD** - Password of the API user.

For  more details about Web-API related configuarion values, see :ref:`here <webapisettings>`.


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

To retrieve this token for subsequent requests, **/api/v1/session** can be called, 
with the credentials defined in **LB_WEB_USER** and **LB_WEB_PWD**.

.. code-block:: bash

    $ curl -XPOST -s -d "username=yourusername&password=yourpassword" \
    http://localhost:8080/api/v1/session

The response returns a **HTTP status 200** contains a JSON document with the token included:

.. code-block:: bash

    {"token": "58725ad5-d669-4431-9991-1a0cff261526"}

This token is stored in memory by the API and will get invalid at restart and after re-requesting a new token.

Control bridges over API
------------------------


**Retrieving current control data**

.. code-block:: bash

    curl -XGET -s -H "X-Auth-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    http://localhost:8080/api/v1/controldata

**Putting new control data**

.. code-block:: bash

    curl -XPUT -v -H "X-Auth-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -T control-api.json \
    http://localhost:8080/api/v1/controldata


