==========
Clustering
==========

Introduction
============
There are some techniques that can be used to enable multiple Web Flayer nodes
to work together using a single database.

The database is node-agnostic, to a degree. When an instance of ``flay`` pops a
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
Web Flayer supports running multiple agents on the same machine, and across
multiple machines.

By default Web Flayer will run under an ``id`` of ``unknown``. While not
technically required, it is highly recommended that you use a different ``id``
for each agent that connects to the database.

The agent is normally set inside the configuration file:

.. code-block:: yaml

    id: myagent

When starting Web Flayer as a daemon, a different configuration file may be
specified:

.. code-block:: bash

    $ flay --daemon --config-file /etc/flay/custom

Multiple configuration files may be set up, for multiple agents. However, it
is likely that the same configuration will be desired for each agent. In this
case, a single configuration file may be used, with a different ``id`` in it.

Keep in mind that when running as a daemon, Web Flayer sets up a local web
server for management purposes. When running multiple daemons on the same
machine, each agent must use a different port.

.. code-block:: bash

    $ flay --daemon --id hydrogen --api-port 1138
    $ flay --daemon --id helium --api-port 1139
    $ flay --daemon --id lithium --api-port 1140

When multiple agents are running on the same machine, management commands (such
as ``stop``) must also include the ``id`` for individual agents:

.. code-block:: bash

    $ flay --stop --id hydrogen


Refresh Interval
================
When adding an item to the queue, it is possible to set a ``refresh_interval``.
This is a dictionary, stored in the database as JSON data. Therefore, specifying
an interval must be done in JSON:

.. code-block:: bash

    $ flay --refresh-interval '{"days": 7}' http://example.com/path

The above example will queue the URL for immediate retrieval. When it is
processed, it will be added back to the queue, with a ``paused_until`` value
that is 7 days from now. The following time intervals may be specified:

* seconds
* minutes
* hours
* days
* weeks


Waiting
=======
The more clients that try to hit a domain at once, the more of a chance of,
intentionally or not, creating a denial of service attack against that domain.
Web Flayer has the ability to wait, not just on a per-agent, but on a
per-cluster basis, to wait between attempts against remote servers.

domain_wait
-----------
By default, there is no wait between any request. However, configuring the
``domain_wait`` option will cause the database to log a domain name, and the
next time that domain is available for retreival. This value is configured as
a number of seconds.

.. code-block:: yaml

    domain_wait: 5

.. code-block:: bash

    $ flay --domain-wait 5

When ``domain_wait`` is configured, all domains will be subject to its rules.
For more specific rules, see ``pattern_wait``.

pattern_wait
------------
There may be situations where a more configurable wait period is needed. For
instances, you may want URLs that are known to contain media to have a longer
wait between retrievals. This is where ``pattern_wait`` comes into play.

The type of pattern specified in ``pattern_wait`` is a regular expression.
If you're not good with regular expressions, that okay. You don't need to use
fancy wildcards or anything; just a domain name will work:

.. code-block:: yaml

    example.com

``pattern_wait`` isn't a command line option, because it's intended to contain
a larger and more permanent collection of patterns. Instead, a table in the
database is maintained which contains these patterns, and their wait period
(in seconds).

There are two fields in the ``pattern_wait`` table: ``pattern`` and ``wait``.

.. code-block:: sql

    INSERT INTO pattern_wait (pattern, wait) VALUES ('example.com', 60)

Unlike ``domain_wait``, ``pattern_wait`` is applied to the entire URL, not
just the domain, so the following patterns are also acceptable:

    * ``mp4$``
    * ``example\.com.*\.mp4``
    * ``https.*mp4``
