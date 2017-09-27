.. :changelog::

Changelog
---------

0.6.2 - `master`_
-----------------

.. note:: This version is not yet released and is under active development.

0.6.1 Sep 27, 2017
------------------

Bugfixes
++++++++
- Add proper formatting for the modification time (if-modified-since header)
 
 
0.6.0 Jul 14, 2017
~~~~~~~~~~~~~~~~~

Features
++++++++

- Add dependency on certifi
- Update certificate bundle as a fallback, will be deprecated.
- Adapt parsing of the cert bundle for twisted http client.


0.5.5 Apr 20, 2017
~~~~~~~~~~~~~~~~~

- Add a bonafide status event.

0.5.4 Mar 17, 2017
~~~~~~~~~~~~~~~~~~

- Add a vpn status event.

0.5.3 Mar 13, 2017
~~~~~~~~~~~~~~~~~~

- Add mail_status_changed event.

0.5.2 Jul 11, 2016
~~~~~~~~~~~~~~~~~~

- Remove dependency on dirspec

0.5.1 Apr 18, 2016
~~~~~~~~~~~~~~~~~~

Features
++++++++

- Add HookableService, allowing inter-service notification for hooks.
- Get events working on windows.
- Optional flag to disable curve authentication.


Bugfixes
++++++++

- `#7536 <https://leap.se/code/issues/7536>`_: zmq authenticator often hangs.


0.5.0 Nov 11, 2015
~~~~~~~~~~~~~~~~~~

Features
++++++++

- `#7523 <https://leap.se/code/issues/7523>`_: Allow to skip the twisted version check, needed to run soledad-client sync tests in the platform with the twisted versions in wheezy.

Misc
++++

- Bump version to 0.5.0, to correct a versioning mistake in the debian packages.
- Rename extras to 'http' and document dependencies on the README.
- Migrate changelog to rst.

.. _`master`: https://0xacab.org/leap/leap_pycommon
