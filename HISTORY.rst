0.4.4 Oct 28, 2015
++++++++++++++++++
- Consider standalone flag when saving events certificates. Related `#7512 <https://leap.se/code/issues/7512>`_.
- fix wrong ca_cert path inside bundle.
- Workaround for deadlock problem in zmq auth.

0.4.3 Sep 22, 2015
++++++++++++++++++
- Expose async methods for events. Closes: `#7274 <https://leap.se/code/issues/7274>`_.

0.4.2 Aug 26, 2015
++++++++++++++++++
- Add http request timeout. Related to `#7234 <https://leap.se/code/issues/7234>`_.
- Add a flag to disable events framework. Closes:`#7259 <https://leap.se/code/issues/7259>`_
- Allow passing callback to HTTP client.
- Bugfix: do not add a port string to non-tcp addresses.
- Add close method for http agent.
- Fix code style and tests.
- Bugfix: HTTP timeout was not being cleared on abort.

0.4.1 Jul 10, 2015
++++++++++++++++++
- Fix regexp to allow ipc protocol in zmq sockets. Closes: `#7089 <https://leap.se/code/issues/7089>`_.
- Remove extraneous data from events logs. Closes `#7130 <https://leap.se/code/issues/7130>`_.
- Make https client use Twisted SSL validation and adds a reuse by default behavior on connection pool

0.4.0 Jun 1, 2015
+++++++++++++++++
- Modify leap.common.events to use ZMQ. Closes `#6359 <https://leap.se/code/issues/6359>`_.
- Fix time comparison between local and UTC times that caused the VPN certificates not being correctly downloaded on time. Closes `#6994 <https://leap.se/code/issues/6994>`_.
- Add a HTTPClient the twisted way.

0.3.10 Jan 26, 2015
+++++++++++++++++++
- Consider different possibilities for tmpdir. Related to `#6631 <https://leap.se/code/issues/6631>`_.
- Add support for deferreds to memoize_method decorator
- Extract the environment set up and tear down for tests

====
2014
====

0.3.9 Jul 18, 2014
++++++++++++++++++
- Include pemfile in the package data. Closes `#5897 <https://leap.se/code/issues/5897>`_.
- Look for bundled cacert.pem in the Resources dir for OSX.

0.3.8 Jun 6, 2014
+++++++++++++++++
- Add Soledad sync status signals. Closes `#5517 <https://leap.se/code/issues/5517>`_.

0.3.7 Apr 4, 2014
+++++++++++++++++
- Add memoized_method decorator. Closes `#4784 <https://leap.se/code/issues/4784>`_.
- Add Soledad invalid auth token event. Closes `#5191 <https://leap.se/code/issues/5191>`_.
- Support str type in email charset detection.

====
2013
====

0.3.6 Dec 6, 2013
+++++++++++++++++
- Update some documentation and packaging bits.

0.3.5 Nov 1, 2013
+++++++++++++++++
- Move get_email_charset to this module.

0.3.4 Oct 4, 2013
+++++++++++++++++
- Add cert bundle including ca-cert certificate. Closes `#3850 <https://leap.se/code/issues/3850>`_.

0.3.3 Sep 20, 2013
++++++++++++++++++
- Fix events server exception raising when port is occupied by some other process. Closes `#3515 <https://leap.se/code/issues/3515>`_.

0.3.2 Sep 06, 2013
++++++++++++++++++
- Use dirspec instead of plain xdg. Closes `#3574 <https://leap.se/code/issues/3574>`_.
- Correct use of CallbackAlreadyRegistered exception.

0.3.1 Aug 23, 2013
++++++++++++++++++
- Add libssl-dev requirement for pyOpenSSL.
- Make the server ping call be async inside events' ensure_server. Fixes `#3355 <https://leap.se/code/issues/3355>`_.
- Requirements in setup are taken from requirements.pip
- Updated requirements.
- Add IMAP_UNREAD_MAIL event.
- Add events for SMTP relay signaling. Closes `#3464 <https://leap.se/code/issues/3464>`_.
- Add events for imap and keymanager notifications. Closes:`#3480 <https://leap.se/code/issues/3480>`_
- Add versioneer to handle versioning.

0.3.0 Aug 9, 2013
+++++++++++++++++
- OSX: Fix problem with path prefix not returning the correct value. Fixes `#3273 <https://leap.se/code/issues/3273>`_.
- Check if schema exists before load a config. Related to `#3310 <https://leap.se/code/issues/3310>`_.
- Handle schemas and api versions in base class. Related to `#3310 <https://leap.se/code/issues/3310>`_.

0.2.7 Jul 26, 2013
++++++++++++++++++
- Refactor events so components are now called clients. Closes `#3246 <https://leap.se/code/issues/3246>`_
- Add leap_check helper method, to use whenever leap_assert does not apply. Related to `#3007 <https://leap.se/code/issues/3007>`_.

0.2.6 Jul 12, 2013
++++++++++++++++++
- Improve leap_assert so that it only prints the traceback from the leap_assert call up. Closes `#2895 <https://leap.se/code/issues/2895>`_
- Add OSX temp directories to the basetests class.

0.2.5 Jun 28, 2013
++++++++++++++++++
- Bugfix: use the provider's default language as default string. Also take care (and note) a possible case with a problematic provider misconfiguration. Closes `#3029 <https://leap.se/code/issues/3029>`_.
- Add data files to setup and manifest (certificates for tests)
- Allow absolute paths in baseconfig.load
- Fix deprecation warnings
- Fix attempt to fetch private keys from server.
- Fix missing imports
- Add possibility of unregistering callbacks for a signal.
- Add a mechanism for events signaling between components.
- Prioritize the path_extension in the which method so it finds our bundled app before the system one, if any.
- Move the Key Manager to leap client repository.
- Move symmetric encryption code to leap.soledad.
- Refactor opengpg utility functions implementation so it uses a context manager.
- Add OpenPGP sign/verify
- Add RAISE_WINDOW event
- Add AES-256 (CTR mode) encrypting/decrypting functions using PyCrypto.
