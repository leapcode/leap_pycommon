# -*- coding: utf-8 -*-
# server.py
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
A server for the events mechanism.

A server can receive different kinds of requests from clients:

  1. Registration request: store client port number to be notified when
     a specific signal arrives.

  2. Signal request: redistribute the signal to registered clients.
"""
import logging
import socket


from protobuf.socketrpc import RpcService
from leap.common.events import (
    events_pb2 as proto,
    daemon,
)


logger = logging.getLogger(__name__)


SERVER_PORT = 8090

# the `registered_clients` dictionary below should have the following
# format:
#
#     { event_signal: [ port, ... ], ... }
#
registered_clients = {}


class PortAlreadyTaken(Exception):
    """
    Raised when trying to open a server in a port that is already taken.
    """
    pass


def ensure_server(port=SERVER_PORT):
    """
    Make sure the server is running on the given port.

    Attempt to connect to given local port. Upon success, assume that the
    events server has already been started. Upon failure, start events server.

    :param port: the port in which server should be listening
    :type port: int

    :return: the daemon instance or nothing
    :rtype: EventsServerDaemon or None

    :raise PortAlreadyTaken: Raised if C{port} is already taken by something
                             that is not an events server.
    """
    try:
        # check if port is available
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        s.close()
        # port is taken, check if there's a server running there
        ping(port,
             reqcbk=lambda req, res: process_ping(port, req, res),
             timeout=10)
    except socket.error:
        # port is available, run a server
        logger.info('Launching server on port %d.', port)
        return EventsServerDaemon.ensure(port)

def process_ping(port, request, response):
    """
    Response callback for the ping event.

    :param port: Port that is trying to be used
    :type port: int
    :param request: Ping request made
    :type request: proto.PingRequest
    :param response: Response from the event
    :type response: proto.EventResponse
    """
    if response is not None and response.status == proto.EventResponse.OK:
        logger.info('A server is already running on port %d.', port)
        return
    # port is taken, and not by an events server
    logger.info('Port %d is taken by something not an events server.', port)
    raise PortAlreadyTaken(port)


def ping(port=SERVER_PORT, reqcbk=None, timeout=1000):
    """
    Ping the server.

    :param port: the port in which server should be listening
    :type port: int
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(proto.PingRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    :return: the response from server for synch calls or nothing for asynch
             calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    request = proto.PingRequest()
    service = RpcService(
        proto.EventsServerService_Stub,
        port,
        'localhost')
    logger.info("Pinging server in port %d..." % port)
    return service.ping(request, callback=reqcbk, timeout=timeout)


class EventsServerService(proto.EventsServerService):
    """
    Service for receiving events in clients.
    """

    def register(self, controller, request, done):
        """
        Register a client port to be signaled when specific events come in.

        :param controller: used to mediate a single method call
        :type controller: protobuf.socketrpc.controller.SocketRpcController
        :param request: the request received from the client
        :type request: leap.common.events.events_pb2.RegisterRequest
        :param done: callback to be called when done
        :type done: protobuf.socketrpc.server.Callback
        """
        logger.info("Received registration request: %s..." % str(request)[:40])
        # add client port to signal list
        if request.event not in registered_clients:
            registered_clients[request.event] = set([])
        registered_clients[request.event].add(request.port)
        # send response back to client

        logger.debug('sending response back')
        response = proto.EventResponse()
        response.status = proto.EventResponse.OK
        done.run(response)

    def unregister(self, controller, request, done):
        """
        Unregister a client port so it will not be signaled when specific
        events come in.

        :param controller: used to mediate a single method call
        :type controller: protobuf.socketrpc.controller.SocketRpcController
        :param request: the request received from the client
        :type request: leap.common.events.events_pb2.RegisterRequest
        :param done: callback to be called when done
        :type done: protobuf.socketrpc.server.Callback
        """
        logger.info(
            "Received unregistration request: %s..." % str(request)[:40])
        # remove client port from signal list
        response = proto.EventResponse()
        if request.event in registered_clients:
            try:
                registered_clients[request.event].remove(request.port)
                response.status = proto.EventResponse.OK
            except KeyError:
                response.status = proto.EventsResponse.ERROR
                response.result = 'Port %d not registered.' % request.port
        # send response back to client
        logger.debug('sending response back')
        done.run(response)

    def signal(self, controller, request, done):
        """
        Perform an RPC call to signal all clients registered to receive a
        specific signal.

        :param controller: used to mediate a single method call
        :type controller: protobuf.socketrpc.controller.SocketRpcController
        :param request: the request received from the client
        :type request: leap.common.events.events_pb2.SignalRequest
        :param done: callback to be called when done
        :type done: protobuf.socketrpc.server.Callback
        """
        logger.info('Received signal from client: %s...', str(request)[:40])
        # send signal to all registered clients
        # TODO: verify signal auth
        if request.event in registered_clients:
            for port in registered_clients[request.event]:

                def callback(req, resp):
                    logger.info("Signal received by " + str(port))

                service = RpcService(proto.EventsClientService_Stub,
                                     port, 'localhost')
                service.signal(request, callback=callback)
        # send response back to client
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
        logger.info("Received ping request, sending response.")
        response = proto.EventResponse()
        response.status = proto.EventResponse.OK
        done.run(response)


class EventsServerDaemon(daemon.EventsSingletonDaemon):
    """
    Singleton class for starting an events server daemon.
    """

    @classmethod
    def ensure(cls, port):
        """
        Make sure the daemon is running on the given port.

        :param port: the port in which the daemon should listen
        :type port: int

        :return: a daemon instance
        :rtype: EventsServerDaemon
        """
        return cls.ensure_service(port, EventsServerService())
