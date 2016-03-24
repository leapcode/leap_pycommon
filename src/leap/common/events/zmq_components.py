# -*- coding: utf-8 -*-
# zmq.py
# Copyright (C) 2015, 2016 LEAP
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
The server for the events mechanism.
"""
import os
import logging
import txzmq
import re

from abc import ABCMeta

try:
    import zmq.auth
    from leap.common.events.auth import TxAuthenticator
    from leap.common.events.auth import TxAuthenticationRequest
except ImportError:
    pass

from txzmq.connection import ZmqEndpoint, ZmqEndpointType

from leap.common.config import flags, get_path_prefix
from leap.common.zmq_utils import zmq_has_curve
from leap.common.zmq_utils import maybe_create_and_get_certificates
from leap.common.zmq_utils import PUBLIC_KEYS_PREFIX

logger = logging.getLogger(__name__)

ADDRESS_RE = re.compile("^([a-z]+)://([^:]+):?(\d+)?$")

LOCALHOST_ALLOWED = '127.0.0.1'


class TxZmqComponent(object):
    """
    A twisted-powered zmq events component.
    """
    _factory = txzmq.ZmqFactory()
    _factory.registerForShutdown()
    _auth = None

    __metaclass__ = ABCMeta

    _component_type = None

    def __init__(self, path_prefix=None, enable_curve=True, factory=None):
        """
        Initialize the txzmq component.
        """
        if path_prefix is None:
            path_prefix = get_path_prefix(flags.STANDALONE)
        if factory is not None:
            self._factory = factory
        self._config_prefix = os.path.join(path_prefix, "leap", "events")
        self._connections = []
        if enable_curve:
            self.use_curve = zmq_has_curve()
        else:
            self.use_curve = False

    @property
    def component_type(self):
        if not self._component_type:
            raise Exception(
                "Make sure implementations of TxZmqComponent"
                "define a self._component_type!")
        return self._component_type

    def _zmq_bind(self, connClass, address):
        """
        Bind to an address.

        :param connClass: The connection class to be used.
        :type connClass: txzmq.ZmqConnection
        :param address: The address to bind to.
        :type address: str

        :return: The binded connection and port.
        :rtype: (txzmq.ZmqConnection, int)
        """
        proto, addr, port = ADDRESS_RE.search(address).groups()

        endpoint = ZmqEndpoint(ZmqEndpointType.bind, address)
        connection = connClass(self._factory)

        if self.use_curve:
            socket = connection.socket

            public, secret = maybe_create_and_get_certificates(
                self._config_prefix, self.component_type)
            socket.curve_publickey = public
            socket.curve_secretkey = secret
            self._start_authentication(connection.socket)

        if proto == 'tcp' and int(port) == 0:
            connection.endpoints.extend([endpoint])
            port = connection.socket.bind_to_random_port('tcp://%s' % addr)
        else:
            connection.addEndpoints([endpoint])

        return connection, int(port)

    def _zmq_connect(self, connClass, address):
        """
        Connect to an address.

        :param connClass: The connection class to be used.
        :type connClass: txzmq.ZmqConnection
        :param address: The address to connect to.
        :type address: str

        :return: The binded connection.
        :rtype: txzmq.ZmqConnection
        """
        endpoint = ZmqEndpoint(ZmqEndpointType.connect, address)
        connection = connClass(self._factory)

        if self.use_curve:
            socket = connection.socket
            public, secret = maybe_create_and_get_certificates(
                self._config_prefix, self.component_type)
            server_public_file = os.path.join(
                self._config_prefix, PUBLIC_KEYS_PREFIX, "server.key")

            server_public, _ = zmq.auth.load_certificate(server_public_file)
            socket.curve_publickey = public
            socket.curve_secretkey = secret
            socket.curve_serverkey = server_public

        connection.addEndpoints([endpoint])
        return connection

    def _start_authentication(self, socket):

        if not TxZmqComponent._auth:
            TxZmqComponent._auth = TxAuthenticator(self._factory)
            TxZmqComponent._auth.start()

        auth_req = TxAuthenticationRequest(self._factory)
        auth_req.start()
        auth_req.allow(LOCALHOST_ALLOWED)

        # tell authenticator to use the certificate in a directory
        public_keys_dir = os.path.join(self._config_prefix, PUBLIC_KEYS_PREFIX)
        auth_req.configure_curve(domain="*", location=public_keys_dir)
        auth_req.shutdown()
        TxZmqComponent._auth.shutdown()

        # This has to be set before binding the socket, that's why this method
        # has to be called before addEndpoints()
        socket.curve_server = True


class TxZmqServerComponent(TxZmqComponent):
    """
    A txZMQ server component.
    """

    _component_type = "server"


class TxZmqClientComponent(TxZmqComponent):
    """
    A txZMQ client component.
    """

    _component_type = "client"
