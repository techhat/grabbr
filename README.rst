=================
Grabbr Web Spider
=================

Grabbr is a web spider that makes use of the Salt loader system to determine
which sites to process, and how.

Don't get too attached to the name; it's likely to change.


Database
========
Grabbr requires PostgreSQL. Schema can be found in the schema directory.


Configuration
=============
The configuration file is located at ``/etc/grabbr/grabbr``, and is in YAML
format. The following settings are required:

.. code-block:: yaml

    dbhost: <database hostname>
    dbname: <database name>
    dbuser: <database user>
    dbpass: <database password>

The following settings are also configurable:

.. code-block:: yaml

    pid_file: /var/run/grabbr/pid
    module_dir: /srv/grabbr-plugins
    force: False
    random_sleep: False
    headers:
        User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11

Plugins may also declare their own settings inside the configuration file.


Plugins
=======
Plugins are stored in ``/srv/grabbr-plugins``. Each plugin _must_ have a
function called ``func_map()`` which examines a URL and returns whether or not
that module can handle it, and if so, which function to run for it. This
function might look like:

.. code-block:: python

    def fun_map(url):
        if 'mysite.com' in url:
            return process_mysite

This states that if a URL contains ``mysite.com``, then the ``process_mysite``
function should be run. Make sure to pass the function object
(``process_mysite``) and not the contents of the function
(``process_mysite()``).

There may also optionally be a function called ``pre_flight``. This function is
meant to check the URL and perform any last-minute operations before parsing
the page. This is largely useful for processing a URL that should not be
cached, such as one that is expected to have dynamic data. This function might
look like:

.. code-block:: python

    def pre_flight(url_id, url):
        if 'mysite.com' in url and '/dynamic/' in url:
            url_id = 0
            content = ''
        return url_id, url, content

The above function would look at the URL and decide whether it looks like a page
is expected to be dynamic. If so, it sets the ``url_id`` to ``0`` and the
``content`` to an empty string. When Grabbr later looks at the ``url_id`` and
sees that it is already set to ``0``, it will skip caching the data.

This function must always accept ``url_id`` and ``url``.

Beyond these two functions, any other non-internal functions are expected to
be used to perform actual parsing and processing tasks.

These (and all non-dunder) functions have the following built-in variables
available to them:

* ``__config__``: A reference to the Grabbr configuration
* ``__urls__``: A reference to the in-memory URL queue (but not the database queue)
* ``__dbclient__``: A reference to the database client object

The following variables are required in the function declaration:

* ``url_id``: The ``url_id`` for the database record
* ``url``: The URL being processed
* ``content``: The content of the URL being processed

These functions do not return any data. They process the content and perform
whatever action is necessary (mining more URLs, downloading media files, saving
necessary data to a file or database, etc).

If a function finds more URLs that need to be processed, it may append them 
directly to the ``__urls__`` list, and they will be processed in turn. However,
it is better to add then directly to the database by calling ``queue_urls``
from the ``grabbr.tools`` module:

.. code-block:: python

    import grabbr.tools
    grabbr.tools.queue_urls(new_urls, __dbclient__, __config__)
