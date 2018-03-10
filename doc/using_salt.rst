==========
Using Salt
==========
Grabbr makes use of Salt's loader system in order to load plugins. It is only
natural that other Salt functionality also be available for Grabbr.

Grains
======
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
                api_host:
                    127.0.0.1
                api_port:
                    1138
                dbname:
                    grabbr
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
                    grabbr
                dbhost:
                    localhost
                id:
                    nitrogen
                pid:
                    26167

These data are used by the execution module to communicate with Grabbr.


Execution Module
================
The ``grabbr`` execution module is used to control Grabbr on remote minions.
An ``id_`` should be specified for most commands, but if it is not, Salt will
try and guess what ``id_`` to use, based on actively running agents on the
machine. If it is unable to do so, it will return an error.

Functions
---------
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
``/srv/grabbr/parsers``. If it is specified here or in the ``config_file``
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
~~~~~~~~~~~~~~~~
List current active downloads.

.. code-block:: bash

    $ salt-call --local grabbr.active_downloads


Events
======
Grabbr has the ability to fire events on the Salt event bus. This functionality
is new, but will be built up over time. The following event is available:

* ``grabbr/{id}/download``

Where ``{id}`` refers to the ID of the grabbr agent, configured as ``id`` in
the ``grabbr`` configuration file. The data for this event will contain the
original URL that was requested (which may differ from the actual URL that is
being downloaded, such as with redirects) and either ``started`` or ``comlete``.

Setup
-----
In order to use Salt events, set ``salt_events`` to ``True``, either on the
command line or in the ``grabbr`` configuration file.

.. code-block:: bash

    $ grabbr --salt-events ...

.. code-block:: yaml

    salt_events: True

Grabbr will use Salt's ``minion`` configuration file to determine the settings
to use for the event bus, such as the location of the socket files that Salt
uses for communication.

Using these files can be a bit tricky though. For security reasons, these files,
which are owned by whatever user Salt is running on (such as ``salt`` or
``root``), have their mode set to ``0o0600``. This means that the user that
owns them has read and write access, and nobody else has any access.

This is okay if Grabbr is running as either ``salt`` or ``root``, but in a
secure environment, this is not likely to be the case. However, using Linux
FACLs (file access control lists) to add extra user permissions will allow
the Grabbr user to access the event bus. There are still security considerations
to be taken into account, which should be looked at on a case-by-case basis.

Assuming Grabbr is running as the ``grabbr`` user, and the default locations
are used, the following command (run as Salt's user) will allow access:

.. code-block:: bash

    setfacl -m u:grabbr:rw /var/run/salt/minion/*

This must be done each time the minion is started, so setting up a startup
state is not a bad idea. More information can be found in the Salt
documentation:

https://docs.saltstack.com/en/latest/ref/states/startup.html

Usage
-----
If set in the ``grabbr`` configuration file as above, Salt events will be
fired for every download that uses the internal ``status()`` function. This
usually is used by various plugins to download media files.

Firing events for a single URL is done with the ``--salt-events`` flag, as
shown above. 

To see events as they are fired, you can use the ``state`` runner on the master:

.. code-block:: bash

    $ salt-run state.event
    grabbr/flay/download	{"_stamp": "2018-03-10T18:05:20.842966", "pretag": null, "cmd": "_minion_event", "tag": "grabbr/flay/download", "data": {"https://example.com/index.html": "started"}, "id": "flay"}
    grabbr/flay/download	{"_stamp": "2018-03-10T18:05:21.007295", "pretag": null, "cmd": "_minion_event", "tag": "grabbr/flay/download", "data": {"https://example.com/index.html": "complete"}, "id": "flay"}
