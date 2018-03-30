==========
Using Salt
==========
Web Flayer makes use of Salt's loader system in order to load plugins. It is only
natural that other Salt functionality also be available for Web Flayer.

Grains
======
Certain pieces of information about Web Flayer are available to Salt using the
``grains`` module that ships with it.

.. code-block:: bash

    $ salt-call --local grains.item flayer_agents
    local:
        ----------
        flayer_agents:
            ----------
            hydrogen:
                ----------
                api_host:
                    127.0.0.1
                api_port:
                    1138
                dbname:
                    flayer
                dbhost:
                    localhost
                id:
                    carbon
                pid:
                    26040
            helium:
                ----------
                api_host:
                    127.0.0.1
                api_port:
                    1139
                dbname:
                    flayer
                dbhost:
                    localhost
                id:
                    nitrogen
                pid:
                    26167

These data are used by the execution module to communicate with Web Flayer.


Execution Module
================
The ``flayer`` execution module is used to control Web Flayer on remote minions.
An ``id_`` should be specified for most commands, but if it is not, Salt will
try and guess what ``id_`` to use, based on actively running agents on the
machine. If it is unable to do so, it will return an error.

Functions
---------
The following functions are available to the ``flayer`` execution module:

queue
~~~~~
Queue a URL for download. It will be processed up by the next available agent.
It is not possible to specify which agent (``id_``) should handle it.

.. code-block:: bash

    $ salt-call --local flayer.queue http://example.com

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

Any additional data that may need to be passed to Web Flayer. This is nor normally
used.

start
~~~~~
Start a ``flay`` agent on the minion.

.. code-block:: bash

    $ salt-call --local flayer.start id_=hydrogen api_port=1138

Parameters:

config_file
```````````
Optional ``str``, default ``/etc/flayer/flayer``.

Location of the configuration file.

run_dir
```````
Optional ``str``, default ``/var/run/flayer``.

Location of the ``run_dir``. This is where files such as ``pid`` and ``meta``
are stored. The ``id_`` will be joined to this path.

module_dir
``````````
Optional ``list``, default ``None``.

An alternate location for Web Flayer modules. If this is not specified here, or in
the ``config_file`` then it will be set to a list containing a single item of
``/srv/flayer/parsers``. If it is specified here or in the ``config_file``
then that location will not be implicitly included (meaning you need to specify
it along with your other paths if you want to use it).

id_
```
Optional ``str``, default ``None``.

The ``id`` to start the Web Flayer agent as.

api_addr
````````
Optional ``str``, default ``127.0.0.1``.

The host to bind the new Web Flayer agent to. Because this is not a secure
connection, it should not be set to anything other than ``127.0.0.1``.

api_port
````````
Optional ``int``, default ``424242``.

The port to bind the new Web Flayer agent to. This should be specified for each new
Web Flayer agent, unless already configured in the ``config_file``.


stop
~~~~
Stop the ``flay`` agent on the minion.

.. code-block:: bash

    $ salt-call --local flayer.stop hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Web Flayer agent to stop.

hard_stop
~~~~~~~~~
Stop the ``flay`` agent on the minion.

.. code-block:: bash

    $ salt-call --local flayer.hard_stop hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Web Flayer agent to hard stop.

abort
~~~~~
Abort the ``flay`` agent on the minion.

.. code-block:: bash

    $ salt-call --local flayer.abort hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Web Flayer agent to abort.

show_opts
~~~~~~~~~
List the opts for the Web Flayer agent.

.. code-block:: bash

    $ salt-call --local flayer.show_opts hydrogen

Parameters:

id_
```
Optional ``str``, default ``None``.

The ``id`` of the Web Flayer agent to abort.

list_queue
~~~~~~~~~~
List the contents of the download queue.

.. code-block:: bash

    $ salt-call --local flayer.list_queue 

active_downloads
~~~~~~~~~~~~~~~~
List current active downloads.

.. code-block:: bash

    $ salt-call --local flayer.active_downloads


Events
======
Web Flayer has the ability to fire events on the Salt event bus. This functionality
is new, but will be built up over time. The following event is available:

* ``flayer/{id}/download``

Where ``{id}`` refers to the ID of the ``flay`` agent, configured as ``id`` in
the ``flayer`` configuration file. The data for this event will contain the
original URL that was requested (which may differ from the actual URL that is
being downloaded, such as with redirects) and either ``started`` or
``complete``.

Setup
-----
In order to use Salt events, set ``salt_events`` to ``True``, either on the
command line or in the ``flayer`` configuration file.

.. code-block:: bash

    $ flay --salt-events ...

.. code-block:: yaml

    salt_events: True

Web Flayer will use Salt's ``minion`` configuration file to determine the settings
to use for the event bus, such as the location of the socket files that Salt
uses for communication.

Using these files can be a bit tricky though. For security reasons, these files,
which are owned by whatever user Salt is running on (such as ``salt`` or
``root``), have their mode set to ``0o0600``. This means that the user that
owns them has read and write access, and nobody else has any access.

This is okay if Web Flayer is running as either ``salt`` or ``root``, but in a
secure environment, this is not likely to be the case. However, using Linux
FACLs (file access control lists) to add extra user permissions will allow
the Web Flayer user to access the event bus. There are still security considerations
to be taken into account, which should be looked at on a case-by-case basis.

Assuming Web Flayer is running as the ``flayer`` user, and the default locations
are used, the following command (run as Salt's user) will allow access:

.. code-block:: bash

    setfacl -m u:flayer:rw /var/run/salt/minion/*

This must be done each time the minion is started, so setting up a startup
state is not a bad idea. More information can be found in the Salt
documentation:

https://docs.saltstack.com/en/latest/ref/states/startup.html

Usage
-----
If set in the ``flayer`` configuration file as above, Salt events will be
fired for every download that uses the internal ``status()`` function. This
usually is used by various plugins to download media files.

Firing events for a single URL is done with the ``--salt-events`` flag, as
shown above. 

To see events as they are fired, you can use the ``state`` runner on the master:

.. code-block:: bash

    $ salt-run state.event
    flayer/flay/download	{"_stamp": "2018-03-10T18:05:20.842966", "pretag": null, "cmd": "_minion_event", "tag": "flayer/flay/download", "data": {"https://example.com/index.html": "started"}, "id": "flay"}
    flayer/flay/download	{"_stamp": "2018-03-10T18:05:21.007295", "pretag": null, "cmd": "_minion_event", "tag": "flayer/flay/download", "data": {"https://example.com/index.html": "complete"}, "id": "flay"}
