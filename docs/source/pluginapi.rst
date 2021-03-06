.. _pluginapi:

Plugin API
----------

BaseSource
~~~~~~~~~~

.. autoclass:: livebridge.base.BaseSource
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

   .. autoattribute:: livebridge.base.BaseSource.type
      :annotation: = Defines source type
   .. autoattribute:: livebridge.base.BaseSource.mode
      :annotation: = Defines source mode
   .. automethod:: livebridge.base.BaseSource.__init__

.. autoclass:: livebridge.base.PollingSource
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

.. autoclass:: livebridge.base.StreamingSource
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

BasePost
~~~~~~~~

.. autoclass:: livebridge.base.BasePost
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
   :private-members:

   .. autoattribute:: livebridge.base.BasePost.source
      :annotation: = Defines source type
   .. automethod:: livebridge.base.BasePost.__init__

BaseConverter
~~~~~~~~~~~~~
.. autoclass:: livebridge.base.BaseConverter
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

   .. autoattribute:: livebridge.base.BaseConverter.source
      :annotation: = Specifies the type of the source post
   .. autoattribute:: livebridge.base.BaseConverter.target
      :annotation: = Specifies the target type of the conversion

ConversionResult
~~~~~~~~~~~~~~~~
.. autoclass:: livebridge.base.ConversionResult
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

BaseTarget
~~~~~~~~~~
.. autoclass:: livebridge.base.BaseTarget
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

   .. autoattribute:: livebridge.base.BaseTarget.type
      :annotation: = Defines target type
   .. automethod:: livebridge.base.BaseTarget.__init__

TargetResponse
~~~~~~~~~~~~~~
.. autoclass:: livebridge.base.TargetResponse
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

InvalidTargetResource
~~~~~~~~~~~~~~~~~~~~~
.. autoexception:: livebridge.base.InvalidTargetResource
   :members:

BaseStorage
~~~~~~~~~~~
.. autoclass:: livebridge.storages.base.BaseStorage
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
