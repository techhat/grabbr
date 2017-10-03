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
