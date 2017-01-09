.. _control:

Control bridges
===============

The **livebridge** command expects a **-control=** parameter, specifying the path to a control file with the \
configuration for the content bridges.

**--control** can be either a **local control file** or a **remote control file** on **s3**:

* with local control file

.. code-block:: bash

    livebridge --control=/path/to/control.yaml

* with remote control file on S3

.. code-block:: bash

    livebridge --control=s3://bucketname/control.yaml

.. note::
  The control file can alternatively be specified via the **LB_CONTROLFILE** environment variable.


The bridges, over which the content is syndicated, are setup in this control file in *YAML* format. Use \
`control.yaml.example`_ as basis for your own control file.

.. code-block:: yaml

    auth:
        dev:
            user: "dev"
            password: "pwd"
            api_key: "F00Baz"
        live:
            user: "prod"
            password: "pwd2"
            api_key: "Foobar"
    bridges:
        - source_id: "abcdefg"
          endpoint:  "https://example.com/api/"
          label: "Example 1"
          targets:
            - type: "scribble"
              event_id: "123456"
              auth: "dev"
            - type: "another"
              event_id: "654321"
              auth: "live"
        - source_id: 54321
          endpoint:  "https://foo.org/api/"
          label: "Example 2"
          targets:
            - type: "scribble"
              event_id: "123456"
              auth: "dev"

Authorization
-------------
    
Credentials for service authorization are defined under **auth:**, in which the keys \
like **dev** or **live** are later used for reference under **bridges:** and **targets:**. 

Bridges
-------

One or more bridges can be controlled under **bridges:**.

Mandatory for every source or target is **type:**, which is a string and has to match the values \
of :py:attr:`livebridge.base.BaseSource.type` or :py:attr:`livebridge.base.BaseTarget.type` of the \
described concrete source or target plugin.

All configuration values besides **type:** will be turned over to the concrete target and source classes as \
**__init__** parameter **config**.

If there's an **auth:** value for the source or target, the value will be matched to a block under **auth:** \
and these values will be merged under **auth:** of the source/target. For example the last target from the example above will be \
resolved from **Livebridge** to following Python dict structure:

.. code-block:: python 

    { 
        'type': 'scribble',
        'event_id': '123456',
        'auth': {
            'user': 'dev',
            'password': 'pwd',
            'api_key': 'F00Baz'
        }
    }

Sources
-------

A block for a source consists of parameter for the source and one or multiple **targets:** blocks.

Targets
-------

A block for a target consists of parameter for the target.

.. _`control.yaml.example`: https://github.com/dpa-newslab/livebridge/blob/master/control.yaml.example
