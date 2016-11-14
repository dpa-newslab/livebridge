.. _ownplugins:

Writing own service plugins
===========================

The name of your Python module has to start with **livebridge_**, so it can be discovered at start time. For example **livebridge_slack**, **livebridge_scribblelive** or **livebridge_liveblog**.

The module has also be available in `PYTHONPATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_ to be discovered.

See :ref:`Tutorial: How to build a Livebridge plugin <tutorial>`

plugin components
-----------------
There are four different components, which a custom plugin module can provide:

* **Source** - implements the way a service is checked for new posts, must be inherited from :class:`livebridge.base.BaseSource`.
* **Post** - implements access to data from a source post, defined by :class:`livebridge.base.BasePost`
* **Converter** - implements a conversion from a specific source to a specific target, has to be inherited \
  from :class:`livebridge.base.BaseConverter`.
* **Target** - implements the create, update and delete *(CRUD)* actions against a target API, has to be inherited from :class:`livebridge.base.BaseTarget`. 

To announce these components to **Livebridge**, so they can be used and defined in a \
:ref:`control file <control>`, they have to be available as direct submodule of your plugin module. 

For example in an imagined **livebridge_acme** plugin module the following should \
be in **livebridge_acme/__init__.py**:

.. code-block:: python
   :linenos:

   # makes Acme service available as source
   from livebridge_acme.source import AcmeSource 
   # defines access to data from Acme posts
   from livebridge_acme.post import AcmePost
   # converter from Acme to Foo
   from livebridge_acme.converter import AcmeToFooConverter
   # make Acme service available as target.
   from livebridge_acme.target import AcmeTarget
    
Examples: 

* https://github.com/dpa-newslab/livebridge-slack/blob/master/livebridge_slack/__init__.py

* https://github.com/dpa-newslab/livebridge-slack/blob/master/livebridge_scibblelive/__init__.py

* https://github.com/dpa-newslab/livebridge-liveblog/blob/master/livebridge_scibblelive/__init__.py


API
---

.. toctree::
   :maxdepth: 2

   pluginapi
