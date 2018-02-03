====================
Grabbr Configuration
====================

Introduction
============

There are multiple ways to configure Grabbr. It is important to understand each
of these methods, before looking at the configuration options themselves.

Configuration File
------------------
The base configuration for Grabbr comes from the configuration file. Normally
this is located at ``/etc/grabbr/grabbr``, but the location can be changed
using the ``--config-file`` argument on the command line:

.. code-block:: bash

    grabbr --config-file /path/to/config http://example.com/

This file is in YAML format. A small example file might look like:

.. code-block:: yaml

    id: flay
    dbhost: localhost
    dbname: grabbr
    dbuser: postgres
    dbpass: ''

Configuration in this file will override any defaults that are used inside
Grabbr itself.

Environment Variables
---------------------
Environment variables are a popular way to configure programs on a per-user
basis, without modifying any configuration files. Any option that can be read
from the command line can be defined as an environment variable, by uppercasing
the name and prepending it with ``GRABBR_``. For instance, a ``.bash_profile``
file would define the above values as:

.. code-block:: bash

    EXPORT GRABBR_ID=flay
    EXPORT GRABBR_DBHOST=localhost
    EXPORT GRABBR_DBNAME=grabbr
    EXPORT GRABBR_DBUSER=postgres
    EXPORT GRABBR_DBPASS=''

Environment variables will override any configuration specified in the
configuration file.

Command Line Options
--------------------
Configuration may also be passed into Grabbr from the command line. Any item
that is configured via configuration files or environment variables will be
overridden if specified from the command line. However, not all command line
options are used for configuration. Many options are used for run-time only. 
Configuration options, as well as run-time options, are described below.

In order to make Grabbr as user-friendly as possible, any command line options
that are analogous to an option in wget will be used, when appropriate. There
are some options that don't match up. Those, and the reasoning for their
deviation, are described in the Grabbr vs Wget document.

API Configuration
-----------------
Grabbr runs a tiny web server, which can be used to set configuration in
real-time. By default this server runs on port ``42424``, and is bound to
``127.0.0.1``. Because there is no security (authentication, HTTPS, etc), it is
highly recommended that you do _not_ change these settings. However, if you
need to, they are as follows:

.. code-block:: yaml

    api_addr: 127.0.0.1
    api_port: 42424

This interface is very simple. Configuration is passed in as name=value pairs
via a GET method, and the configuration will be updated.

.. code-block::

    http://localhost:42424/?user_agent=mygrabbr

The API can also be used to issue a ``stop`` (or ``hard_stop`` or ``abort``)
command to Grabbr:

.. code-block::

    http://localhost:42424/?stop=True

And finally, the API can be used to add URLs to the download queue:

.. code-block::

   http://localhost:42424/?queue=True&urls=http%3A%2F%2Fexample.com


Configuration Options
=====================
The following options are available for Grabbr.

config_file
~~~~~~~~~~~
CLI Option: ``--config-file``
Default: ``/etc/grabbr/grabbr``

Location for the config file.

pid_file
~~~~~~~~
CLI Option: ``--pid-file``
Default: /var/run/grabbr/pid

Location for the PID file.

module_dir
~~~~~~~~~~
CLI Option: ``--module-dir``
Default: ``[/srv/grabbr-plugins]``

Location for grabbr plugins.

daemon
~~~~~~
CLI Option: ``--daemon``
Default: ``False``

Start as a background service.

Stopping Grabbr
---------------

stop
~~~~
CLI Option: ``--stop``

Stop Grabbr after the current download, rather than moving to the next item in
the queue.

hard_stop
~~~~~~~~~
CLI Option: ``--hard-stop``

Stop Grabbr, delete and requeue the current download, then exit.

abort
~~~~~
CLI Option: ``--abort``

Stop Grabbr, delete current download, then exit.

stop_file
~~~~~~~~~
CLI Option: ``--stop-file``
Default: ``/var/run/grabbr/stop``

Location of the stop file. This file is used by Grabbr as a flag to know that
a stop has been requested.

force
~~~~~
CLI Option: ``-f``, ``--force'``
Default: ``False``

Force grabbr to re-download the URL(s). Normally URLs that have been processed
are described in the database, and will not be downloaded again unless forced.

wait
~~~~
CLI Option: ``-w``, ``--wait``
Default: 0

Amount of time to wait between requests. Analogous to ``--wait`` in wget.

random_wait
~~~~~~~~~~~
CLI Option: ``--random-wait``
Default: ``False``

Random wait (default from 1 to 10 seconds) between requests. Based on
``--random-wait`` in wget.

single
~~~~~~
CLI Option: ``-s``, ``--single``
Default: ``False``

Process a single URL, separate from any other current processes. This ignores
the ``pid_file``, ``stop_file``, etc. If multiple URLs are specified when
using this option, only the first will be used.

include_headers
~~~~~~~~~~~~~~~
CLI Option: ``-S``, ``--server-response``
Default: ``False``

Display (using pprint) the headers when requesting a URL.

verbose
~~~~~~~
CLI Option: ``-v``, ``--verbose``
Default: ``False``

Display more information about what's going on.

input_file
~~~~~~~~~~
CLI Option: ``-i``, ``--input-file``

A file containing a list of URLs to download. Each line contains one URL.  If
``-`` is specified, then URLs will be read from ``STDIN``.

headers
~~~~~~~
CLI Option: ``-H``, ``--header``

A header line to be included with the request. Multiple headers may be added
with this option.

data
~~~~
CLI Option: ``-d``, ``--data``

Data to be POSTed in the request.

use_queue
~~~~~~~~~
CLI Options: ``--use-queue``, ``--no-queue``
Default: ``True``

Process the items in the download queue (default).

queue
~~~~~
CLI Option: ``--queue``

Add the URLs to the download queue and exit.

list_queue
~~~~~~~~~~
CLI Option: ``-l``, ``--list-queue``

List the remaining URLS in the download queue.

reprocess
~~~~~~~~~
CLI Option: ``-p``, ``--reprocess``

Reprocess a URL using a postgresql-style regular expression. This implies
``--force``, as it will search through the database for URLs that have already
been processed.

no_db_cache
~~~~~~~~~~~
CLI Option: ``--no-db-cache``
Default: ``False``

Don't cache the target in the database.

source
~~~~~~
CLI Option: ``--source``

Display the URL's source. Analogous to ``-O -`` in wget and ``-source`` in
elinks.

render
~~~~~~
CLI Option: ``--render``, ``--dump``

Render the content, as it would display in a browser. Analogous to ``-dump`` in
elinks. Unlike elinks, does not add a list of links to the end.

links
~~~~~
CLI Option: ``--links``

Display by a list of the absolute URLs in the page. Analogous to using ``dump``
in elinks to retreive a list of links.

queuelinks
~~~~~~~~~~
CLI Option: ``--queue-links``
Default: ``False``

Add the absolute URLs from the page to the download queue. By default a page
will be processed, but links will not be followed.

queue_re
~~~~~~~~
CLI Option: ``--queue-re``, ``--queue-regex``, ``--queue-regexp``

When using ``--queue-links``, add the absolute URLs matching the regexp to the
download queue.

search_src
~~~~~~~~~~
CLI Option: ``--search-src``
Default: ``False``

When using ``--queue-links``, search tags with ``src`` attribute, in addition
to ``href`` s.

force_directories
~~~~~~~~~~~~~~~~~
CLI Option: ``-x``, ``--force-directories``
Default: ``False``

When downloading, force a directory structure, based on the hostname, port (if
present), and path found in the URL.

save_path
~~~~~~~~~
CLI Option: ``--save-path``

When downloading, use this path as the download root. The default for this path
may differ based on the plugin that processes the URL, but normally the current
working directory (``./``) will be used.

save_html
~~~~~~~~~
CLI Option: ``--save-html``, ``--no-save-html``
Default: ``True``

When downloading, save HTML as well as binary files.

rename_template
~~~~~~~~~~~~~~~
CLI Option: ``--rename``, ``--rename-template``

A template to use for renaming downloads. Variables in this template are
enclosed with braces (``{`` and ``}``).

rename_count_start
~~~~~~~~~~~~~~~~~~
CLI Option: ``--rename-count-start``
Default: 0

When using ``rename_template``, a ``{count}`` may be used. This is the number
to start ``{count}`` at.

rename_count_padding
~~~~~~~~~~~~~~~~~~~~
CLI Option: ``--rename-count-padding``
Default: 0

Zero-padding to be used for ``{count}``

level
~~~~~
CLI Option: ``--level``
Default: 0 (disabled)

Specify recursion maximum depth level depth.

span_hosts
~~~~~~~~~~
CLI Option: ``--span-hosts``
Default: ``False``

Enable spanning across hosts when doing recursive retrieving.

use_plugins
~~~~~~~~~~~
CLI Option: ``--use-plugins``, ``--no-plugins``
Default: ``True``

Download the URL, using the plugins to process it (default).

user_agent
~~~~~~~~~~
CLI Option: ``--user-agent``
Default: ``grabbr``

Send this user agent string to the server.
