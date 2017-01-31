.. _adapter:

Plugin for services
===================

Following plugins are currently available:

* **Liveblog** livebridge-liveblog_ - Provides a Liveblog_ liveticker as source and target.
* **Scribblelive** livebridge-scribblelive_ - Provides a Scribblelive_ event stream as target. \
  Provides also a **converter** from Liveblog_ to Scribblelive_.
* **Slack** livebridge-slack_  - Provides Slack_ channels as source and as target. Also provides \
  **converters** from Liveblog_ and to Scribblelive_. 
* **Tickaroo** livebridge-tickaroo_ - Provides a Tickaroo_ ticker as target.


Installing plugins
------------------
    
Plugins **can** be made available from PyPi_ to be installable via **pip**.

For example to install a **Livebridge** with plugins for Liveblog_ and Scribblelive_:

.. code-block:: bash

   pip3 install livebridge livebridge-liveblog livebridge-scribblelive


Control plugins
---------------

See :ref:`control` for setting up bridges.

.. include:: links.rst
