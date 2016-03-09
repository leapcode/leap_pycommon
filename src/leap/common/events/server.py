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
The server for the events mechanism.
"""
import logging
import platform

import txzmq

from leap.common.zmq_utils import zmq_has_curve
from leap.common.events.zmq_components import TxZmqServerComponent


if zmq_has_curve() or platform.system() == "Windows":
    # Windows doesn't have ipc sockets, we need to use always tcp
    EMIT_ADDR = "tcp://127.0.0.1:9000"
    REG_ADDR = "tcp://127.0.0.1:9001"
else:
    EMIT_ADDR = "ipc:///tmp/leap.common.events.socket.0"
    REG_ADDR = "ipc:///tmp/leap.common.events.socket.1"

logger = logging.getLogger(__name__)


def ensure_server(emit_addr=EMIT_ADDR, reg_addr=REG_ADDR, path_prefix=None,
                  factory=None, enable_curve=True):
    """
    Make sure the server is running in the given addresses.

    :param emit_addr: The address in which to receive events from clients.
    :type emit_addr: str
    :param reg_addr: The address to which publish events to clients.
    :type reg_addr: str

    :return: an events server instance
    :rtype: EventsServer
    """
    _server = EventsServer(emit_addr, reg_addr, path_prefix, factory=factory,
                           enable_curve=enable_curve)
    return _server


class EventsServer(TxZmqServerComponent):
    """
    An events server that listens for events in one address and publishes those
    events in another address.
    """

    def __init__(self, emit_addr, reg_addr, path_prefix=None, factory=None,
                 enable_curve=True):
        """
        Initialize the events server.

        :param emit_addr: The address in which to receive events from clients.
        :type emit_addr: str
        :param reg_addr: The address to which publish events to clients.
        :type reg_addr: str
        """
        TxZmqServerComponent.__init__(self, path_prefix=path_prefix,
                                      factory=factory,
                                      enable_curve=enable_curve)
        # bind PULL and PUB sockets
        self._pull, self.pull_port = self._zmq_bind(
            txzmq.ZmqPullConnection, emit_addr)
        self._pub, self.pub_port = self._zmq_bind(
            txzmq.ZmqPubConnection, reg_addr)
        # set a handler for arriving messages
        self._pull.onPull = self._onPull

    def _onPull(self, message):
        """
        Callback executed when a message is pulled from a client.

        :param message: The message sent by the client.
        :type message: str
        """
        event, content = message[0].split(b"\0", 1)
        logger.debug("Publishing event: %s" % event)
        self._pub.publish(content, tag=event)
