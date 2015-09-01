Events mechanism
================

The events mechanism allows for clients to send events to each other by means
of a centralized server. Clients can register with the server to receive
events of certain types, and they can also send events to the server that will
then redistribute these events to registered clients.


ZMQ connections and events redistribution
-----------------------------------------

Clients and server use ZMQ connection patterns to communicate. Clients can
push events to the server, and may subscribe to events published by the
server. The server in turn pulls events from clients and publishes them to
subscribed clients.

Clients connect to the server's zmq pub socket, and register to specific
events indicating which callbacks should be executed when that event is
received:


                               EventsServer
                              .------------.
                              |PULL     PUB|
                              '------------'
                                         ^^
                                         ||
                            reg(1, cbk1) |'--------------. reg(2, cbk2)
                                         |               |
                                         |               |
            .------------.    .------------.   .------------.
            |PUSH     SUB|    |PUSH     SUB|   |PUSH     SUB|
            '------------'    '------------'   '------------'
             EventsClient      EventsClient     EventsClient


A client that wants to send an event connects to the server's zmq pull socket
and pushes the event to the server. The server then redistributes it to all
clients subscribed to that event.


                               EventsServer
                              .------------.
                              |PULL---->PUB|
                              '------------'
                               ^         |.
                               |         |.
sig(1, 'foo') .----------------'         |'...............
              |                          |               .
              |                          v               .
            .------------.    .------------.   .------------.
            |PUSH     SUB|    |PUSH     SUB|   |PUSH     SUB|
            '------------'    '------------'   '------------'
             EventsClient      EventsClient     EventsClient
                                    |
                                    v
                              cbk1(1, 'foo')


Any client may emit or subscribe to an event. ZMQ will manage sockets and
reuse the connection whenever it can.


                               EventsServer
                              .------------.
                              |PULL---->PUB|
                              '------------'
                                ^        .|
                                |        .|
sig(2, 'bar') .-----------------'        .'--------------.
              |                          .               |
              |                          .               v
            .------------.    .------------.   .------------.
            |PUSH     SUB|    |PUSH     SUB|   |PUSH     SUB|
            '------------'    '------------'   '------------'
             EventsClient      EventsClient     EventsClient
                                                     |
                                                     v
                                               cbk2(2, 'bar')


How to use it
-------------

To start the events server:

>>> from leap.common.events import server
>>> server.ensure_server(
        emit_addr="tcp://127.0.0.1:9000",
        reg_addr="tcp://127.0.0.1:9001")

To register a callback to be called when a given event is raised:

>>> from leap.common.events import register
>>> from leap.common.events import catalog
>>>
>>> def mycbk(event, *content):
>>>     print "%s, %s" (str(event),  str(content))
>>>
>>> register(catalog.CLIENT_UID, callback=mycbk)

To emit an event:

>>> from leap.common.events import emit
>>> from leap.common.events import catalog
>>> emit(catalog.CLIENT_UID)

Adding events
-------------

To add a new event, just add it to ``catalog.py``.
