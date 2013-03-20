# -*- coding: utf-8 -*-
# service.py
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

import logging
import threading
from protobuf.socketrpc.server import (
    SocketRpcServer,
    ThreadedTCPServer,
    SocketHandler,
)
from leap.common.events import (
    signal_pb2 as proto,
    registered_callbacks,
)


logger = logging.getLogger(__name__)


class SignalRpcServer(SocketRpcServer):

    def __init__(self, port, host='localhost'):
        '''port - Port this server is started on'''
        self.port = port
        self.host = host
        self.serviceMap = {}
        self.server = None

    def run(self):
        '''Activate the server.'''
        logger.info('Running server on port %d' % self.port)
        self.server = ThreadedTCPServer((self.host, self.port),
                                        SocketHandler, self)
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class SignalService(proto.SignalService):
    '''
    Handles signaling for LEAP components.
    '''

    def signal(self, controller, request, done):
        logger.info('Received signal.')

        # Run registered callbacks
        if registered_callbacks.has_key(request.signal):
            for (_, cbk) in registered_callbacks[request.signal]:
                cbk(request)

        # Create response message
        response = proto.SignalResponse()
        # TODO: change id for something meaningful
        response.id = 1
        response.status = proto.SignalResponse.OK

        # Call provided callback with response message
        done.run(response)


class SignalServiceThread(threading.Thread):
    """
    Singleton class for starting a server thread
    """

    # Singleton instance
    _instance = None

    def __init__(self, port):
        super(SignalServiceThread, self).__init__()
        self._service = SignalService()
        self._port = port
        self._server = SignalRpcServer(self._port)
        self._server.registerService(self._service)
        self.setDaemon(True)

    @staticmethod
    def start_service(port):
        """
        Start the singleton instance if not already running
        Will not exit until the process ends
        """
        if SignalServiceThread._instance == None:
            SignalServiceThread._instance = SignalServiceThread(port)
            SignalServiceThread._instance.start()
        elif port != SignalServiceThread._instance._port:
            # TODO: make this exception more self-explanatory
            raise Exception()
        return SignalServiceThread._instance

    def get_instance(self):
        return self._instance

    def run(self):
        self._server.run()

    def stop(self):
        self._server.stop()
