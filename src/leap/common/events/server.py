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

A server can receive different kinds of requests from components:

  1. Registration request: store component port number to be notified when
     a specific signal arrives.

  2. Signal request: redistribute the signal to registered components.
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

# the `registered_components` dictionary below should have the following
# format:
#
#     { event_signal: [ port, ... ], ... }
#
registered_components = {}


def ensure_server(port=SERVER_PORT):
    """
    Make sure the server is running on the given port.

    Attempt to connect to given local port. Upon success, assume that the
    events server has already been started. Upon failure, start events server.

    @param port: the port in which server should be listening
    @type port: int

    @return: the daemon instance or nothing
    @rtype: EventsServerDaemon or None
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        s.close()
        logger.info('Server is already running on port %d.', port)
        return None
    except socket.error:
        logger.info('Launching server on port %d.', port)
        return EventsServerDaemon.ensure(port)


class EventsServerService(proto.EventsServerService):
    """
    Service for receiving events in components.
    """

    def register(self, controller, request, done):
        """
        Register a component port to be signaled when specific events come in.

        @param controller: used to mediate a single method call
        @type controller: protobuf.socketrpc.controller.SocketRpcController
        @param request: the request received from the component
        @type request: leap.common.events.events_pb2.RegisterRequest
        @param done: callback to be called when done
        @type done: protobuf.socketrpc.server.Callback
        """
        logger.info("Received registration request: %s" % str(request))
        # add component port to signal list
        if request.event not in registered_components:
            registered_components[request.event] = set([])
        registered_components[request.event].add(request.port)
        # send response back to component

        logger.debug('sending response back')
        response = proto.EventResponse()
        response.status = proto.EventResponse.OK
        done.run(response)

    def signal(self, controller, request, done):
        """
        Perform an RPC call to signal all components registered to receive a
        specific signal.

        @param controller: used to mediate a single method call
        @type controller: protobuf.socketrpc.controller.SocketRpcController
        @param request: the request received from the component
        @type request: leap.common.events.events_pb2.SignalRequest
        @param done: callback to be called when done
        @type done: protobuf.socketrpc.server.Callback
        """
        logger.info('Received signal from component: %s', str(request))
        # send signal to all registered components
        # TODO: verify signal auth
        if request.event in registered_components:
            for port in registered_components[request.event]:

                def callback(req, resp):
                    logger.info("Signal received by " + str(port))

                service = RpcService(proto.EventsComponentService_Stub,
                                     port, 'localhost')
                service.signal(request, callback=callback)
        # send response back to component
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

        @param port: the port in which the daemon should listen
        @type port: int

        @return: a daemon instance
        @rtype: EventsServerDaemon
        """
        return cls.ensure_service(port, EventsServerService())
