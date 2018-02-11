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

Refresh Interval
----------------
When adding an item to the queue, it is possible to set a ``refresh_interval``.
This is a dictionary, stored in the database as JSON data. Therefore, specifying
an interval must be done in JSON:

.. code-block:: bash

    grabbr --refresh-interval '{"days": 7}' http://example.com/path

The above example will queue the URL for immediate retrieval. When it is
processed, it will be added back to the queue, with a ``paused_until`` value
that is 7 days from now. The following time intervals may be specified:

* seconds
* minutes
* hours
* days
* weeks
