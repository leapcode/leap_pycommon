.. :changelog::

Changelog
---------

====
2016
====
0.5.2 Jul 11, 2016
++++++++++++++++++
- Remove dependency on dirspec

0.5.1 Apr 18, 2016
+++++++++++++++++++

Features
~~~~~~~~
- Add HookableService, allowing inter-service notification for hooks.
- Get events working on windows.
- Optional flag to disable curve authentication.

Bugfixes
~~~~~~~~
- `#7536 <https://leap.se/code/issues/7536>`_: zmq authenticator often hangs.


====
2015
====


0.5.0 Nov 11, 2015
++++++++++++++++++

Features
~~~~~~~~
- `#7523 <https://leap.se/code/issues/7523>`_: Allow to skip the twisted version check, needed to run soledad-client sync tests in the platform with the twisted versions in wheezy.

Misc
~~~~
- Bump version to 0.5.0, to correct a versioning mistake in the debian packages.
- Rename extras to 'http' and document dependencies on the README.
- Migrate changelog to rst.
