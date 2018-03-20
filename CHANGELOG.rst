0.6.4
=====
Sat Mar 10 2018
---------------
* Add domain_wait to keep from overloading domains
* Store status, and filter unicode null from content
* Add pattern_wait
* Add agent ID to the events
* Fire messages on the salt event bus
* Add db name and host to meta file
* Need a count for queue message
* Make queue message more descriptive
* Add custom search limits
* Rename modules/plugins to parsers
* Add JSON-LD example plugins
* Move plugins into their own tree
* Add organize loader
* Break out loader into its own file
* Add search plugins
* Force a sane mode for new cache_dirs. This wasn't happening in daemon mode.

Contributors:
* Joseph Hall

0.6.2
=====
Sun Feb 18 2018
---------------
* Pass addr and port to salt module (start)
* Don't let agents step on each other
* Control grabbr by ID
* Use common run_dir, write a metadata file
* Add Salt grains for Grabbr metadata
* Add start options to salt execution module
* Show active downloads from salt
* Save download stats in memory
* Pause and unpause URLs
* Show grabbr opts in execution module
* Look at opts while the daemon is running
* Log who is downloading what
* Switch to UUIDs
* Add refresh_interval to download queue

Contributors:
* Joseph Hall

0.6.0 / 0.6.1
=============
Sun Feb 4 2018
--------------
Initial Release

Contributors:
* Joseph Hall
