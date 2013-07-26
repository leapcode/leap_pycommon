# -*- coding: utf-8 -*-
# daemon.py
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
A singleton daemon for running RPC services using protobuf.socketrpc.
"""


import logging
import threading


from protobuf.socketrpc.server import (
    SocketRpcServer,
    ThreadedTCPServer,
    SocketHandler,
)


logger = logging.getLogger(__name__)


class ServiceAlreadyRunningException(Exception):
    """
    Raised whenever a service is already running in this process but someone
    attemped to start it in a different port.
    """


class EventsRpcServer(SocketRpcServer):
    """
    RPC server used in server and client interfaces to receive messages.
    """

    def __init__(self, port, host='localhost'):
        """
        Initialize a RPC server.

        :param port: the port in which to listen for incoming messages
        :type port: int
        :param host: the address to bind to
        :type host: str
        """
        SocketRpcServer.__init__(self, port, host)
        self._server = None

    def run(self):
        """
        Run the server.
        """
        logger.info('Running server on port %d.' % self.port)
        # parent implementation does not hold the server instance, so we do it
        # here.
        self._server = ThreadedTCPServer((self.host, self.port),
                                         SocketHandler, self)
        # if we chose to use a random port, fetch the port number info.
        if self.port is 0:
            self.port = self._server.socket.getsockname()[1]
        self._server.serve_forever()

    def stop(self):
        """
        Stop the server.
        """
        self._server.shutdown()


class EventsSingletonDaemon(threading.Thread):
    """
    Singleton class for for launching and terminating a daemon.

    This class is used so every part of the mechanism that needs to listen for
    messages can launch its own daemon (thread) to do the job.
    """

    # Singleton instance
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Return a singleton instance if it exists or create and initialize one.
        """
        if len(args) is not 2:
            raise TypeError("__init__() takes exactly 2 arguments (%d given)"
                            % len(args))
        if cls.__instance is None:
            cls.__instance = object.__new__(
                EventsSingletonDaemon)
            cls.__initialize(cls.__instance, args[0], args[1])
        return cls.__instance

    @staticmethod
    def __initialize(self, port, service):
        """
        Initialize a singleton daemon.

        This is a static method disguised as instance method that actually
        does the initialization of the daemon instance.

        :param port: the port in which to listen for incoming messages
        :type port: int
        :param service: the service to provide in this daemon
        :type service: google.protobuf.service.Service
        """
        threading.Thread.__init__(self)
        self._port = port
        self._service = service
        self._server = EventsRpcServer(self._port)
        self._server.registerService(self._service)
        self.daemon = True

    def __init__(self):
        """
        Singleton placeholder initialization method.

        Initialization is made in __new__ so we can always return the same
        instance upon object creation.
        """
        pass

    @classmethod
    def ensure(cls, port):
        """
        Make sure the daemon instance is running.

        Each implementation of this method should call `self.ensure_service`
        with the appropriate service from the `events.proto` definitions, and
        return the daemon instance.

        :param port: the port in which the daemon should be listening
        :type port: int

        :return: a daemon instance
        :rtype: EventsSingletonDaemon
        """
        raise NotImplementedError(self.ensure)

    @classmethod
    def ensure_service(cls, port, service):
        """
        Start the singleton instance if not already running.

        Might return ServiceAlreadyRunningException

        :param port: the port in which the daemon should be listening
        :type port: int

        :return: a daemon instance
        :rtype: EventsSingletonDaemon
        """
        daemon = cls(port, service)
        if not daemon.is_alive():
            daemon.start()
        elif port and port != cls.__instance._port:
            # service is running in this process but someone is trying to
            # start it in another port
            raise ServiceAlreadyRunningException(
                "Service is already running in this process on port %d."
                % self.__instance._port)
        return daemon

    @classmethod
    def get_instance(cls):
        """
        Retrieve singleton instance of this daemon.

        :return: a daemon instance
        :rtype: EventsSingletonDaemon
        """
        return cls.__instance

    def run(self):
        """
        Run the server.
        """
        self._server.run()

    def stop(self):
        """
        Stop the daemon.
        """
        self._server.stop()

    def get_port(self):
        """
        Retrieve the value of the port to which the service running in this
        daemon is binded to.

        :return: the port to which the daemon is binded to
        :rtype: int
        """
        if self._port is 0:
            self._port = self._server.port
        return self._port
