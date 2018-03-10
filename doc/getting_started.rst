===============
Getting Started
===============

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
    parser_dir:
      - /srv/grabbr/parsers
    force: False
    random_wait: False
    headers:
        User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11

Various plugins may also declare their own settings inside the configuration
file.
