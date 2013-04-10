Events mechanism
================

The events mechanism allows for "components" to send signal events to each
other by means of a centralized server. Components can register with the
server to receive signals of certain types, and they can also send signals to
the server that will then redistribute these signals to registered components.


Listening daemons
-----------------

Both components and the server listen for incoming messages by using a
listening daemon that runs in its own thread. The server daemon has to be
started explicitly, while components daemon will be started whenever a
component registers with the server to receive messages.


How to use it
-------------

To start the events server:

>>> from leap.common.events import server
>>> server.ensure_server(port=8090)

To register a callback to be called when a given signal is raised:

>>> from leap.common.events import (
>>>     register,
>>>     events_pb2 as proto,
>>> )
>>>
>>> def mycallback(sigreq):
>>>     print str(sigreq)
>>>
>>> events.register(signal=proto.CLIENT_UID, callback=mycallback)

To signal an event:

>>> from leap.common.events import (
>>>     signal,
>>>     events_pb2 as proto,
>>> )
>>> signal(proto.CLIENT_UID)

Adding events
-------------

* Add the new event under enum ``Event`` in ``events.proto`` 
* Compile the new protocolbuffers file::

  make
