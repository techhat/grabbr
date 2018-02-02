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
    module_dir:
      - /srv/grabbr-plugins
    force: False
    random_wait: False
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

    def func_map(url):
        '''
        Function map
        '''
        if 'wikipedia' in url:
            return wikipedia_raw
        return None

This states that if a URL contains ``wikipedia``, then the ``wikipedia_raw``
function should be called. Make sure to pass the function object
(``wikipedia_raw``) and not the contents of the function
(``wikipedia_raw()``). An example of this function is provided below.

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

Other public functions are expected to be used for processing URLs and their
contents. In order for these functions to be called, they must be mapped in
the ``func_map()`` function as described above.

These (and all non-dunder) functions have the following built-in variables
available to them:

* ``__opts__``: A reference to the Grabbr configuration
* ``__urls__``: A reference to the in-memory URL queue (but not the database queue)
* ``__dbclient__``: A reference to the database client object

The following variables are required in the function declaration:

* ``url_id``: The ``url_id`` for the database record
* ``url``: The URL being processed
* ``content``: The content of the URL being processed

These functions do not return any data. They process the content and perform
whatever action is necessary (mining more URLs, downloading media files, saving
necessary data to a file or database, etc).

Consider the following function:

.. code-block:: python

    def wikipedia_raw(url_id, url, content):
        '''
        Grab raw wikipedia data
        '''
        cache_path = __opts__.get('wikipedia_cache_path', '.')
        title = url.split('?')[0].split('/')[-1]
        file_name = '{}/{}'.format(cache_path, title)
        req = requests.get(url, stream=True, params={'action': 'raw'})
        grabbr.tools.status(req, url, file_name)

In this function, the following will happen:

* First, get the ``cache_path`` from the configuration file. If it isn't there, use the current working directory (``.``).
* Extract the ``title`` of the page from the URL.
* Generate the output file_name using the ``cache_path`` and the ``title``.
* Set up a ``requests`` object to download the raw version of the URL.
* Use ``grabbr.tools.status`` to download the URL. This function is discussed below.

The above function only makes use of the ``url``, and only because it needs to
extract information from that URL. Because the ``content`` of that URL is also
passed in, you may only need your function to process that. The ``url_id`` is
provided in case you need to refer to the URL's location in Grabbr's database.

It is common for data mining tools to collect links while processing a page.
If a function finds more URLs that need to be processed, it may append them 
directly to the ``__urls__`` list, and they will be processed in turn. However,
it is better to add then directly to the database by calling ``queue_urls``
from the ``grabbr.tools`` module:

.. code-block:: python

    import grabbr.tools
    grabbr.tools.queue_urls(new_urls, __dbclient__, __opts__)

The ``grabbr.tools.status`` function is available for URLs that point to a file
that needs to be downloaded to disk. For example, this could be a chunk of
JSON, an image, or a larger file such as a tarball or a video. This function
will not only download that file, but also provide status on the download.

Once a filename has been generated to save the file to, there are two steps
that are performed:

* Set up a requests object to perform the download.
* Pass that object, along with the URL and filename, to the ``status`` function.

Consider the following block of code:

.. code-block:: python

    import requests
    import grabbr.tools
    req = requests.get(url, stream=True)
    grabbr.tools.status(req, url, file_name, opts=__opts__)

First, a ``requests`` object called ``req`` is set up, which ``stream`` set to
``True``. Please note that the ``status`` function requires this to be set.

Then that object, along with the url, the filename, and the ``opts``, is passed
to ``status``, which will perform the download, while generating updates, as
one might expect from a program like ``wget``.
