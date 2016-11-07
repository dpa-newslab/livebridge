.. _adapter:

Plugin for services
===================

Following plugins are currently available:

* **Liveblog** livebridge-liveblog_ - Provides a Liveblog_ liveticker as source.
* **Scribblelive** livebridge-scribblelive_ - Provides a Scribblelive_ event stream as target. \
  Provides also a **converter** from Liveblog_ to Scribblelive_.
* **Slack** livebridge-slack_  - Provides Slack_ channels as source and as target. Also provides \
  **converters** from Liveblog_ and to Scribblelive_. 


Installing plugins
------------------
    
Plugins **should** be available from PyPi_ and installable via **pip**.

For example to install a **Livebridge** with plugins for Liveblog_ and Scribblelive_:

.. code-block:: bash

   pip3 install livebridge livebridge-liveblog livebridge-scribblelive


Control plugins
---------------

See :ref:`control` for setting up bridges.


.. _livebridge-liveblog: https://github.com/dpa-newslab/livebridge-liveblog
.. _livebridge-scribblelive: https://github.com/dpa-newslab/livebridge-scribblelive
.. _livebridge-slack: https://github.com/dpa-newslab/livebridge-slack
.. _Slack: https://slack.com
.. _Liveblog: https://github.com/liveblog/liveblog
.. _Scribblelive: http://scribblelive.com
.. _PyPi: http://pypi.python.org/
