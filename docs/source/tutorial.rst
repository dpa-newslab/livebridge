.. _tutorial:                                        

Tutorial: How to build a Livebridge plugin
==========================================

Livebridge is extensible through plugins. 

The easiest way to create your own plugin is to adapt this `skeleton plugin <https://github.com/dpa-newslab/livebridge-plugin-skeleton>`_ and to modify it for your own needs:
 \

**Setup a development environment**

Follow the steps described here: http://pythonhosted.org/livebridge/developing.html. Don't forget to activate your virtual environment!

.. code-block:: bash

  source .env/bin/activate # activate virtualenv

**Checkout repository**

.. code-block:: bash

    git clone git@github.com:dpa-newslab/livebridge-plugin-skeleton.git

**Install your plugin in develop mode**

In order to get your plugin recognized and included by **livebridge** at startup, install your plugin pro-forma in your Python environment.

.. code-block:: bash

  cd livebridge-plugin-skeleton
  python setup.py develop

This installs our plugin in your virtual Python environment in editable mode!
 \

**Control your livebridge**

A control file with a simple demo bridge is included:

.. code-block:: bash 

 bridges:
     - type: "skeleton"
       label: "SOURCE"
       source_id: "skel-1"
       targets:
         - type: "skeleton"
           label: "TARGET"
           target_id: "skel-2"

**type** is important, it reflects the **type**, **source** or **target** properties of your components. We use the identifier **skeleton** throughout this tutorial, change it later to your own needs.
 \

**So let's start a bridge, to have a look**

.. code-block:: bash

  # first, set two settings
  export LB_DB_DSN=sqlite:///plugin.sqlite 
  export LB_LOGLEVEL=DEBUG 

  # then start your livebridge
  livebridge --control=control.yaml

You'll see some debug output, which tells you, that every 10 seconds a new posting was processed. SQLite is used as storage, a db-file is created in your directory, named **plugin.sqlite**.
 \

**How does it work?**

If you open **livebridge_skeleton/__init__.py** you can see, what and where the parts are:

.. code-block:: python

  from .source import MySource
  from .post import MyPost
  from .converter import MyConverter
  from .target import MyTarget

Here you can see all components used in this merely blank plugin. *See* `<http://pythonhosted.org/livebridge/ownplugins.html>`_ *for an description of the different parts.*
 \

**MySource - the plugin source**

If you want to distribute content from a service with **Livebridge**, you have to  implement a **source**, which looks up a service for new posts. 
 \

Have a look at https://github.com/dpa-newslab/livebridge-plugin-skeleton/blob/master/livebridge_skeleton/source.py to see how this is done:

.. code-block:: python 

    class MySource(StreamingSource):                                           

        type = "skeleton"

        def __init__(self, config):
            self.stopped = False
            self.x_id = 1

        async def listen(self, callback):
            while self.stopped == False:
                self.x_id += 1
                new_post = MyPost({
                    "source_id": "mystream",
                    "id": self.x_id,
                    "text": "skeleton for id {}".format(self.x_id),
                    "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                })
                await callback([new_post])
                await asyncio.sleep(10)
            return True

        async def stop(self):
            self.stopped = True
            return True

What does it? It simulates a streaming source, like a websocket or so. Every 10 seconds a new dummy instance of **MyPost** post is created and a callback method is called with this new post for further processing.
 \

**MyPost - the post class**

To make the targets later on interchangeable, you define a unique interface to your new post(s). We do this by defining our own, from :class:`livebridge.data.TargetPost` derived class:

.. code-block:: python

    class MyPost(BasePost):                                             

        source = "skeleton"

        @property
        def id(self):
            """Return ID of post."""
            return self.data.get("id")

        @property
        def source_id(self):
            """Return ID of the source."""
            return self.data.get("source_id")

        @property
        def created(self):
            """Return created datetime of post."""
            return datetime.strptime(self.data["created"], "%Y-%m-%dT%H:%M:%S+00:00")

        @property
        def updated(self):
            """Return updated datetime of post."""
            return datetime.strptime(self.data["updated"], "%Y-%m-%dT%H:%M:%S+00:00")

        @property
        def is_update(self):
            """Return boolean if post was updated."""
            return bool(self.get_action() == "update")

        @property
        def is_deleted(self):
            """Return boolean if post was deleted."""
            return bool(self.get_action() == "delete")

        @property
        def is_sticky(self):
            """Return boolean if post was set to sticky."""
            return False

        def get_action(self):
            """Return action (create|update|delete|ignore) of post."""
            return "update" if self.get_existing() else "create"

As you can see, the method and the properties are giving access to the correspondent data of your source resource. Why is this important? Because this way you can combine different sources and targets, even without there's a connection in any kind.
 \

If you have source, for which you just want to syndicate content straight forward to targets, without update and delete, you should always return **create** from **get_action**.

 \

**MyConverter - convert the content from the source suitable for your target**

Let's assume, as example, you have written a source component for Twitter updates, and you want to post every new tweet to Facebook. You'll will have to somehow rewrite your tweet. Perhaps you ask "How?", perhaps not, but this way you can do this:

.. code-block:: python 

    class MyConverter(BaseConverter):

        source = "skeleton"
        target = "skeleton"

        async def convert(self, post):
            """Convert incoming raw source post to wanted target."""
            content = "Converted {}".format(post.get("text", "-"))
            return ConversionResult(content=content)

In **convert()** you simply convert your input content to a content suitable for your target. As our small plugin uses itself as source **and** as target, we just do some dummy text conversion. But nonetheless you should understand the principle behind. 
 \

**Imporant**: The class variables **source** and **target** are telling **livebridge**, which conversion this converter provides. In our case, simply from **skeleton** to **skeleton** itself.
 \

**MyTarget - at last, save it in your target**

If you want connect a service as a target to **livebridge**, you have to implement your own target, based on :class:`livebridge.base.BaseTarget`. The idea is the same like in the other parts: you have to implement some necessary methods.

.. code-block:: python

    class MyTarget(BaseTarget):

        type = "skeleton"

        def __init__(self, config):
            self.target_id = "{}-{}".format(self.type, config.get("target_id"))
            self.x_id = 0

        async def _do_action(self, url, data):
            logger.debug("Calling imaginary API with {} {}".format(url, data))
            self.x_id += 1
            demo_resp = {
                "status": "OK",
                "id": self.x_id,
                "body": "Demotext",
            }
            return demo_resp

        async def post_item(self, post):
            """Build your request to create post at service."""
            create_url = "/api/create"
            data = {"text": post.content}
            return TargetResponse(await self._do_action(create_url, data))

        async def update_item(self, post):
            """Build your request to update post at service."""
            update_url = "/api/update"
            data = {"text": post.content, "id": post.data.get("id")}
            return TargetResponse(await self._do_action(update_url, data))

        async def delete_item(self, post):
            """Build your request to update post at service."""
            delete_url = "/api/update"
            data = {"id": post.data.get("id")}
            return TargetResponse(await self._do_action(delete_url, data))

        async def handle_extras(self, post):
            """Do exta actions here if needed.
               Will be called after methods above."""
            return None
 
Should be self-explaining to you, isn't it? You have to implement **post_item()**, **update_item()** and **delete_item()**, to create, update or delete a post at a target service.
 \

**Make it your own plugin**

How can you turn this skeleton plugin completely your own? This way:

* to be able to commit your code to your own repository, remove the **.git** folder 
* rename the folder **livebridge_skeleton** to your own name. 
* **Important**: Your new directory name reflects your Python module name and it has to start with **livebridge_**
* edit **setup.py** and modify it to match your own plugin.
* Choose a **type** identifier for your plugin, to replace **"skeleton"**.
* Replace **"skeleton"** in the **type** class variable of your source with this new identifier.
* Replace **"skeleton"** in the **source** class variable of your post class with your identifier.
* Replace **"skeleton"** in the **source** class variable of your converter class with your identifier, **target** too!
* At last replace **"skeleton"** in **type** class variable of your target class with your plugin identifier.









