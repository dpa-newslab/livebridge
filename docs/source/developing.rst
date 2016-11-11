.. _developing:

Development
===========

Create development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 - Create directory

 .. code-block:: bash

    mkdir lbdev
    cd lbdev
 
 - Setup virtualenv

 .. code-block:: bash

    virtualenv -p /usr/bin/python3 .env

 - Activate virtualenv

 .. code-block:: bash

    . .env/bin/activate

 - Clone repository

 .. code-block:: bash

   git clone git@github.com:dpa-newslab/livebridge.git

 - Install requirements

 .. code-block:: bash

   cd livebridge
   pip install -r requirements.txt

 - Install plugins (when only developing livebridge core)

 .. code-block:: bash

  pip install livebridge-slack  

 - `Create control file <control>`_

\

 - `Setup configuration <quickstart.html#settings>`_

\

 - Run livebridge

 .. code-block:: bash

  ./main.py --control=control-dev.yaml

Add additional plugins for development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 - See :ref:`ownplugins` first.

\

 - Clone plugin repository

 .. code-block:: bash
  
  git clone git@github.com:youruser/reponame.git


 - Change into directory

 .. code-block:: bash

  cd reponame 

 - Install dependencies, be sure virtualenv is activated

 .. code-block:: bash
  
  pip install -r requirements.txt


