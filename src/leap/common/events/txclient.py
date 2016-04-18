# -*- coding: utf-8 -*-
# txclient.py
# Copyright (C) 2013, 2014, 2015 LEAP
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
The client end point of the events mechanism, implemented using txzmq.

Clients are the communicating parties of the events mechanism. They
communicate by sending messages to a server, which in turn redistributes
messages to other clients.

When a client registers a callback for a given event, it also tells the
server that it wants to be notified whenever events of that type are sent by
some other client.
"""
import logging
import pickle

import txzmq

from leap.common.events.zmq_components import TxZmqClientComponent
from leap.common.events.client import EventsClient
from leap.common.events.client import configure_client
from leap.common.events.server import EMIT_ADDR
from leap.common.events.server import REG_ADDR
from leap.common.events import catalog


logger = logging.getLogger(__name__)


__all__ = [
    "configure_client",
    "EventsTxClient",
    "register",
    "unregister",
    "emit",
    "shutdown",
]


class EventsTxClient(TxZmqClientComponent, EventsClient):
    """
    A twisted events client that listens for events in one address and
    publishes those events to another address.
    """

    def __init__(self, emit_addr=EMIT_ADDR, reg_addr=REG_ADDR,
                 path_prefix=None, factory=None, enable_curve=True):
        """
        Initialize the events client.
        """
        TxZmqClientComponent.__init__(
            self, path_prefix=path_prefix, factory=factory,
            enable_curve=enable_curve)
        EventsClient.__init__(self, emit_addr, reg_addr)
        # connect SUB first, otherwise we might miss some event sent from this
        # same client
        self._sub = self._zmq_connect(txzmq.ZmqSubConnection, reg_addr)
        self._sub.gotMessage = self._gotMessage

        self._push = self._zmq_connect(txzmq.ZmqPushConnection, emit_addr)

    def _gotMessage(self, msg, tag):
        """
        Handle an incoming event.

        :param msg: The incoming message.
        :type msg: list(str)
        """
        event = getattr(catalog, tag)
        content = pickle.loads(msg)
        self._handle_event(event, content)

    def _subscribe(self, tag):
        """
        Subscribe to a tag on the zmq SUB socket.

        :param tag: The tag to be subscribed.
        :type tag: str
        """
        self._sub.subscribe(tag)

    def _unsubscribe(self, tag):
        """
        Unsubscribe from a tag on the zmq SUB socket.

        :param tag: The tag to be unsubscribed.
        :type tag: str
        """
        self._sub.unsubscribe(tag)

    def _send(self, data):
        """
        Send data through PUSH socket.

        :param data: The data to be sent.
        :type event: str
        """
        self._push.send(data)

    def _run_callback(self, callback, event, content):
        """
        Run a callback.

        :param callback: The callback to be run.
        :type callback: callable(event, *content)
        :param event: The event to be sent.
        :type event: Event
        :param content: The content of the event.
        :type content: list
        """
        callback(event, *content)

    def shutdown(self):
        EventsClient.shutdown(self)


def register(event, callback, uid=None, replace=False):
    """
    Register a callback to be executed when an event is received.

    :param event: The event that triggers the callback.
    :type event: str
    :param callback: The callback to be executed.
    :type callback: callable(event, content)
    :param uid: The callback uid.
    :type uid: str
    :param replace: Wether an eventual callback with same ID should be
                    replaced.
    :type replace: bool

    :return: The callback uid.
    :rtype: str

    :raises CallbackAlreadyRegisteredError: when there's already a callback
            identified by the given uid and replace is False.
    """
    return EventsTxClient.instance().register(
        event, callback, uid=uid, replace=replace)


def unregister(event, uid=None):
    """
    Unregister callbacks for an event.

    If uid is not None, then only the callback identified by the given uid is
    removed. Otherwise, all callbacks for the event are removed.

    :param event: The event that triggers the callback.
    :type event: str
    :param uid: The callback uid.
    :type uid: str
    """
    return EventsTxClient.instance().unregister(event, uid=uid)


def emit(event, *content):
    """
    Send an event.

    :param event: The event to be sent.
    :type event: str
    :param content: The content of the event.
    :type content: list
    """
    return EventsTxClient.instance().emit(event, *content)


def shutdown():
    """
    Shutdown the events client.
    """
    EventsTxClient.instance().shutdown()


def instance():
    """
    Return an instance of the events client.

    :return: An instance of the events client.
    :rtype: EventsClientThread
    """
    return EventsTxClient.instance()
