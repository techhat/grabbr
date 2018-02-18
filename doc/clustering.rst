==========
Clustering
==========

Introduction
============
There are some techniques that can be used to enable multiple Grabbr nodes to
work together using a single database.

The database is node-agnostic, to a degree. When an instance of Grabbr pops a
URL from the download queue, it first places a lock on the item to ensure that
no other nodes try to process it. This lock contains the name of the node.
The node then performs any queue-specific processing (such as checking the
refresh interval), and then deletes it from the queue as appropriate.

There is no imposed limit on how many nodes may access the database at a time,
which means that multiple nodes may process the database without directly
communicating with each other, or performing scheduling using a controlling
node.


Multiple Agents
===============
Grabbr supports running multiple agents on the same machine, and across
multiple machines.

By default Grabbr will run under an ``id`` of ``unknown``. While not technically 
required, it is highly recommended that you use a different ``id`` for each
agent that connects to the database.

The agent is normally set inside the configuration file:

.. code-block:: yaml

    id: myagent

When starting Grabbr as a daemon, a different configuration file may be
specified:

.. code-block:: bash

    $ grabbr --daemon --config-file /etc/grabbr/custom

Multiple configuration files may be set up, for multiple agents. However, it
is likely that the same configuration will be desired for each agent. In this
case, a single configuration file may be used, with a different ``id`` in it.

Keep in mind that when running as a daemon, Grabbr sets up a local web server
for management purposes. When running multiple daemons on the same machine,
each agent must use a different port.

.. code-block:: bash

    $ grabbr --daemon --id hydrogen --api-port 1138
    $ grabbr --daemon --id helium --api-port 1139
    $ grabbr --daemon --id lithium --api-port 1140

When multiple agents are running on the same machine, management commands (such
as ``stop``) must also include the ``id`` for individual agents:

.. code-block:: bash

    $ grabbr --stop --id hydrogen


Refresh Interval
================
When adding an item to the queue, it is possible to set a ``refresh_interval``.
This is a dictionary, stored in the database as JSON data. Therefore, specifying
an interval must be done in JSON:

.. code-block:: bash

    $ grabbr --refresh-interval '{"days": 7}' http://example.com/path

The above example will queue the URL for immediate retrieval. When it is
processed, it will be added back to the queue, with a ``paused_until`` value
that is 7 days from now. The following time intervals may be specified:

* seconds
* minutes
* hours
* days
* weeks


Using Salt
==========
Grabbr makes use of Salt's loader system in order to load plugins. It is only
natural that other Salt functionality also be available for Grabbr.

Grains
------
Certain pieces of information about Grabbr are available to Salt using the
``grains`` module that ships with it.

.. code-block:: bash

    $ salt-call --local grains.item grabbr_agents
    local:
        ----------
        grabbr_agents:
            ----------
            hydrogen:
                ----------
                api_addr:
                    127.0.0.1
                api_port:
                    1138
                id:
                    carbon
                pid:
                    26040
            helium:
                ----------
                api_addr:
                    127.0.0.1
                api_port:
                    1139
                id:
                    nitrogen
                pid:
                    26167

These data are used by the execution module to communicate with Grabbr.

Execution Module
----------------
The ``grabbr`` execution module is used to control Grabbr on remote minions.
An ``id_`` should be specified for most commands, but if it is not, Salt will
try and guess what ``id_`` to use, based on actively running agents on the
machine. If it is unable to do so, it will return an error.

The following functions are available to the ``grabbr`` execution module:

queue
~~~~~
Queue a URL for download. It will be processed up by the next available agent.
It is not possible to specify which agent (``id_``) should handle it.

.. code-block:: bash

    $ salt-call --local grabbr.queue http://example.com

Parameters:

urls
````
Required ``list``.

One or more URLs to queue.

force
`````
Optional ``bool``, default ``False``.

Force a URL that has already been processed to be processed again.

data
````
Optional ``dict``, default ``None``.

Any additional data that may need to be passed to Grabbr. This is nor normally
used.

start
~~~~~
Start a grabbr agent on the minion.

.. code-block:: bash

    $ salt-call --local grabbr.start id_=hydrogen api_port=1138

Parameters:

config_file
```````````
Optional ``str``, default ``/etc/grabbr/grabbr``.

Location of the configuration file.

run_dir
```````
Optional ``str``, default ``/var/run/grabbr``.

Location of the ``run_dir``. This is where files such as ``pid`` and ``meta``
are stored. The ``id_`` will be joined to this path.

module_dir
``````````
Optional ``list``, default ``None``.

An alternate location for Grabbr modules. If this is not specified here, or in
the ``config_file`` then it will be set to a list containing a single item of
``/srv/grabbr-plugins``. If it is specified here or in the ``config_file``
then that location will not be implicitly included (meaning you need to specify
it along with your other paths if you want to use it).

id_
```
Optional ``str``, default ``None``.

The ``id`` to start the Grabbr agent as.

api_addr
````````
Optional ``str``, default ``127.0.0.1``.

The host to bind the new Grabbr agent to. Because this is not a secure
connection, it should not be set to anything other than ``127.0.0.1``.

api_port
````````
Optional ``int``, default ``424242``.

The port to bind the new Grabbr agent to. This should be specified for each new
Grabbr agent, unless already configured in the ``config_file``.


stop
~~~~
Stop the grabbr agent on the minion.

.. code-block:: bash

    $ salt-call --local grabbr.stop hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Grabbr agent to stop.

hard_stop
~~~~~~~~~
Stop the grabbr agent on the minion.

.. code-block:: bash

    $ salt-call --local grabbr.hard_stop hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Grabbr agent to hard stop.

abort
~~~~~
Abort the grabbr agent on the minion.

.. code-block:: bash

    $ salt-call --local grabbr.abort hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Grabbr agent to abort.

show_opts
~~~~~~~~~
List the opts for the Grabbr agent.

.. code-block:: bash

    $ salt-call --local grabbr.show_opts hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Grabbr agent to abort.

list_queue
~~~~~~~~~~
List the contents of the download queue.

.. code-block:: bash

    $ salt-call --local grabbr.list_queue 

active_downloads
~~~~~~~~~~
List current active downloads.

.. code-block:: bash

    $ salt-call --local grabbr.active_downloads

