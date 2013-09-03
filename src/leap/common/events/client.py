# -*- coding: utf-8 -*-
# client.py
# Copyright (C) 2013 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
The client end point of the events mechanism.

Clients are the communicating parties of the events mechanism. They
communicate by sending messages to a server, which in turn redistributes
messages to other clients.

When a client registers a callback for a given signal, it also tells the
server that it wants to be notified whenever signals of that type are sent by
some other client.
"""

import logging


from protobuf.socketrpc import RpcService

from leap.common.events import events_pb2 as proto
from leap.common.events import server
from leap.common.events import daemon
from leap.common.events import mac_auth


logger = logging.getLogger(__name__)


# the `registered_callbacks` dictionary below should have the following
# format:
#
#     { event_signal: [ (uid, callback), ... ], ... }
#
registered_callbacks = {}


class CallbackAlreadyRegistered(Exception):
    """
    Raised when trying to register an already registered callback.
    """
    pass


def ensure_client_daemon():
    """
    Ensure the client daemon is running and listening for incoming
    messages.

    :return: the daemon instance
    :rtype: EventsClientDaemon
    """
    import time
    daemon = EventsClientDaemon.ensure(0)
    logger.debug('ensure client daemon')

    # Because we use a random port we want to wait until a port is assigned to
    # local client daemon.

    while not (EventsClientDaemon.get_instance() and
               EventsClientDaemon.get_instance().get_port()):
        time.sleep(0.1)
    return daemon


def register(signal, callback, uid=None, replace=False, reqcbk=None,
             timeout=1000):
    """
    Registers a callback to be called when a specific signal event is
    received.

    Will timeout after timeout ms if response has not been received. The
    timeout arg is only used for asynch requests. If a reqcbk callback has
    been supplied the timeout arg is not used. The response value will be
    returned for a synch request but nothing will be returned for an asynch
    request.

    :param signal: the signal that causes the callback to be launched
    :type signal: int (see the `events.proto` file)
    :param callback: the callback to be called when the signal is received
    :type callback: function(leap.common.events.events_pb2.SignalRequest)
    :param uid: a unique id for the callback
    :type uid: int
    :param replace: should an existent callback with same uid be replaced?
    :type replace: bool
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(proto.RegisterRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    Might raise a CallbackAlreadyRegistered exception if there's already a
    callback identified by the given uid and replace is False.

    :return: the response from server for synch calls or nothing for asynch
             calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    ensure_client_daemon()  # so we can receive registered signals
    # register callback locally
    if signal not in registered_callbacks:
        registered_callbacks[signal] = []
    cbklist = registered_callbacks[signal]

    # TODO should check that the callback has the right
    # number of arguments.

    if uid and filter(lambda (x, y): x == uid, cbklist):
        if not replace:
            raise CallbackAlreadyRegistered()
        else:
            registered_callbacks[signal] = filter(lambda(x, y): x != uid,
                                                  cbklist)
    registered_callbacks[signal].append((uid, callback))
    # register callback on server
    request = proto.RegisterRequest()
    request.event = signal
    request.port = EventsClientDaemon.get_instance().get_port()
    request.mac_method = mac_auth.MacMethod.MAC_NONE
    request.mac = ""
    service = RpcService(proto.EventsServerService_Stub,
                         server.SERVER_PORT, 'localhost')
    logger.debug(
        "Sending registration request to server on port %s: %s",
        server.SERVER_PORT,
        str(request)[:40])
    return service.register(request, callback=reqcbk, timeout=timeout)


def unregister(signal, uid=None, reqcbk=None, timeout=1000):
    """
    Unregister a callback.

    If C{uid} is specified, unregisters only the callback identified by that
    unique id. Otherwise, unregisters all callbacks

    :param signal: the signal that causes the callback to be launched
    :type signal: int (see the `events.proto` file)
    :param uid: a unique id for the callback
    :type uid: int
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(proto.UnregisterRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    :return: the response from server for synch calls or nothing for asynch
             calls or None if no callback is registered for that signal or
             uid.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    if signal not in registered_callbacks or not registered_callbacks[signal]:
        logger.warning("No callback registered for signal %d." % signal)
        return None
    # unregister callback locally
    cbklist = registered_callbacks[signal]
    if uid is not None:
        if filter(lambda (cbkuid, _): cbkuid == uid, cbklist) == []:
            logger.warning("No callback registered for uid %d." % st)
            return None
        registered_callbacks[signal] = filter(lambda(x, y): x != uid, cbklist)
    else:
        # exclude all callbacks for given signal
        registered_callbacks[signal] = []
    # unregister port in server if there are no more callbacks for this signal
    if not registered_callbacks[signal]:
        request = proto.UnregisterRequest()
        request.event = signal
        request.port = EventsClientDaemon.get_instance().get_port()
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(proto.EventsServerService_Stub,
                             server.SERVER_PORT, 'localhost')
        logger.info(
            "Sending unregistration request to server on port %s: %s",
            server.SERVER_PORT,
            str(request)[:40])
        return service.unregister(request, callback=reqcbk, timeout=timeout)


def signal(signal, content="", mac_method="", mac="", reqcbk=None,
           timeout=1000):
    """
    Send `signal` event to events server.

    Will timeout after timeout ms if response has not been received. The
    timeout arg is only used for asynch requests.  If a reqcbk callback has
    been supplied the timeout arg is not used. The response value will be
    returned for a synch request but nothing will be returned for an asynch
    request.

    :param signal: the signal that causes the callback to be launched
    :type signal: int (see the `events.proto` file)
    :param content: the contents of the event signal
    :type content: str
    :param mac_method: the method used for auth mac
    :type mac_method: str
    :param mac: the content of the auth mac
    :type mac: str
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(proto.SignalRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    :return: the response from server for synch calls or nothing for asynch
             calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    request = proto.SignalRequest()
    request.event = signal
    request.content = content
    request.mac_method = mac_method
    request.mac = mac
    service = RpcService(proto.EventsServerService_Stub, server.SERVER_PORT,
                         'localhost')
    logger.debug("Sending signal to server: %s", str(request)[:40])
    return service.signal(request, callback=reqcbk, timeout=timeout)


def ping(port, reqcbk=None, timeout=1000):
    """
    Ping a client running in C{port}.

    :param port: the port in which the client should be listening
    :type port: int
    :param reqcbk: a callback to be called when a response from client is
                   received
    :type reqcbk: function(proto.PingRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    :return: the response from client for synch calls or nothing for asynch
             calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    request = proto.PingRequest()
    service = RpcService(
        proto.EventsClientService_Stub,
        port,
        'localhost')
    logger.debug("Pinging a client in port %d..." % port)
    return service.ping(request, callback=reqcbk, timeout=timeout)


class EventsClientService(proto.EventsClientService):
    """
    Service for receiving signal events in clients.
    """

    def __init__(self):
        proto.EventsClientService.__init__(self)

    def signal(self, controller, request, done):
        """
        Receive a signal and run callbacks registered for that signal.

        This method is called whenever a signal request is received from
        server.

        :param controller: used to mediate a single method call
        :type controller: protobuf.socketrpc.controller.SocketRpcController
        :param request: the request received from the client
        :type request: leap.common.events.events_pb2.SignalRequest
        :param done: callback to be called when done
        :type done: protobuf.socketrpc.server.Callback
        """
        logger.debug('Received signal from server: %s...' % str(request)[:40])

        # run registered callbacks
        # TODO: verify authentication using mac in incoming message
        if request.event in registered_callbacks:
            for (_, cbk) in registered_callbacks[request.event]:
                # callbacks should be prepared to receive a
                # events_pb2.SignalRequest.
                cbk(request)

        # send response back to server
        response = proto.EventResponse()
        response.status = proto.EventResponse.OK
        done.run(response)

    def ping(self, controller, request, done):
        """
        Reply to a ping request.

        :param controller: used to mediate a single method call
        :type controller: protobuf.socketrpc.controller.SocketRpcController
        :param request: the request received from the client
        :type request: leap.common.events.events_pb2.RegisterRequest
        :param done: callback to be called when done
        :type done: protobuf.socketrpc.server.Callback
        """
        logger.debug("Received ping request, sending response.")
        response = proto.EventResponse()
        response.status = proto.EventResponse.OK
        done.run(response)


class EventsClientDaemon(daemon.EventsSingletonDaemon):
    """
    A daemon that listens for incoming events from server.
    """

    @classmethod
    def ensure(cls, port):
        """
        Make sure the daemon is running on the given port.

        :param port: the port in which the daemon should listen
        :type port: int

        :return: a daemon instance
        :rtype: EventsClientDaemon
        """
        return cls.ensure_service(port, EventsClientService())
