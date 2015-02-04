# -*- coding: utf-8 -*-
# zmq.py
# Copyright (C) 2015 LEAP
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

# XXX some distros don't package libsodium, so we have to be prepared for
#     absence of zmq.auth
try:
    import zmq.auth
    from zmq.auth.thread import ThreadAuthenticator
except ImportError:
    pass

from leap.common.config import get_path_prefix
from leap.common.zmq_utils import zmq_has_curve
from leap.common.zmq_utils import maybe_create_and_get_certificates
from leap.common.zmq_utils import PUBLIC_KEYS_PREFIX


logger = logging.getLogger(__name__)


ADDRESS_RE = re.compile("(.+)://(.+):([0-9]+)")


class TxZmqComponent(object):
    """
    A twisted-powered zmq events component.
    """

    __metaclass__ = ABCMeta

    _component_type = None

    def __init__(self, path_prefix=None):
        """
        Initialize the txzmq component.
        """
        self._factory = txzmq.ZmqFactory()
        self._factory.registerForShutdown()
        if path_prefix == None:
            path_prefix = get_path_prefix()
        self._config_prefix = os.path.join(path_prefix, "leap", "events")
        self._connections = []

    @property
    def component_type(self):
        if not self._component_type:
            raise Exception(
                "Make sure implementations of TxZmqComponent"
                "define a self._component_type!")
        return self._component_type

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
        connection = connClass(self._factory)
        # create and configure socket
        socket = connection.socket
        if zmq_has_curve():
            public, secret = maybe_create_and_get_certificates(
                self._config_prefix, self.component_type)
            server_public_file = os.path.join(
                self._config_prefix, PUBLIC_KEYS_PREFIX, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            socket.curve_publickey = public
            socket.curve_secretkey = secret
            socket.curve_serverkey = server_public
        socket.connect(address)
        logger.debug("Connected %s to %s." % (connClass, address))
        self._connections.append(connection)
        return connection

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
        connection = connClass(self._factory)
        socket = connection.socket
        if zmq_has_curve():
            public, secret = maybe_create_and_get_certificates(
                self._config_prefix, self.component_type)
            socket.curve_publickey = public
            socket.curve_secretkey = secret
            self._start_thread_auth(connection.socket)
        # check if port was given
        protocol, addr, port = ADDRESS_RE.match(address).groups()
        if port == "0":
            port = socket.bind_to_random_port("%s://%s" % (protocol, addr))
        else:
            socket.bind(address)
            port = int(port)
        logger.debug("Binded %s to %s://%s:%d."
                     % (connClass, protocol, addr, port))
        self._connections.append(connection)
        return connection, port

    def _start_thread_auth(self, socket):
        """
        Start the zmq curve thread authenticator.

        :param socket: The socket in which to configure the authenticator.
        :type socket: zmq.Socket
        """
        authenticator = ThreadAuthenticator(self._factory.context)
        authenticator.start()
        # XXX do not hardcode this here.
        authenticator.allow('127.0.0.1')
        # tell authenticator to use the certificate in a directory
        public_keys_dir = os.path.join(self._config_prefix, PUBLIC_KEYS_PREFIX)
        authenticator.configure_curve(domain="*", location=public_keys_dir)
        socket.curve_server = True  # must come before bind

    def shutdown(self):
        """
        Shutdown the component.
        """
        logger.debug("Shutting down component %s." % str(self))
        for conn in self._connections:
            conn.shutdown()
        self._factory.shutdown()


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
