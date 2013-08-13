# -*- coding: utf-8 -*-
# __init__.py
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
This is an events mechanism that uses a server to allow for signaling of
events between clients.

Application components should use the interface available in this file to
register callbacks to be executed upon receiving specific signals, and to send
signals to other components.

To register a callback to be executed when a specific event is signaled, use
leap.common.events.register():

>>> from leap.common.events import register
>>> from leap.common.events.proto import CLIENT_UID
>>> register(CLIENT_UID, lambda req: do_something(req))

To signal an event, use leap.common.events.signal():

>>> from leap.common.events import signal
>>> from leap.common.events.proto import CLIENT_UID
>>> signal(CLIENT_UID)


NOTE ABOUT SYNC/ASYNC REQUESTS:

Clients always communicate with the server, and never between themselves.
When a client registers a callback for an event, the callback is saved locally
in the client and the server stores the client socket port in a list
associated with that event. When a client signals an event, the server
forwards the signal to all registered client ports, and then each client
executes its callbacks associated with that event locally.

Each RPC call from a client to the server is followed by a response from the
server to the client. Calls to register() and signal() (and all other RPC
calls) can be synchronous or asynchronous meaning if they will or not wait for
the server's response before returning.

This mechanism was built on top of protobuf.socketrpc, and because of this RPC
calls are made synchronous or asynchronous in the following way:

  * If RPC calls receive a parameter called `reqcbk`, then the call is made
    asynchronous. That means that:

        - an eventual `timeout` parameter is not used,
        - the call returns immediatelly with value None, and
        - the `reqcbk` callback is executed asynchronously upon the arrival of
          a response from the server.

  * Otherwise, if the `reqcbk` parameter is None, then the call is made in a
    synchronous manner:

        - if a response from server arrives within `timeout` milliseconds, the
          RPC call returns it;
        - otherwise, the call returns None.
"""

import logging
import socket


from leap.common.events import (
    events_pb2 as proto,
    server,
    client,
    daemon,
)


logger = logging.getLogger(__name__)


def register(signal, callback, uid=None, replace=False, reqcbk=None,
             timeout=1000):
    """
    Register a callback to be called when the given signal is received.

    Will timeout after timeout ms if response has not been received. The
    timeout arg is only used for asynch requests. If a reqcbk callback has
    been supplied the timeout arg is not used. The response value will be
    returned for a synch request but nothing will be returned for an asynch
    request.

    :param signal: the signal that causes the callback to be launched
    :type signal: int (see the `events.proto` file)
    :param callback: the callback to be called when the signal is received
    :type callback: function
    :param uid: a unique id for the callback
    :type uid: int
    :param replace: should an existent callback with same uid be replaced?
    :type replace: bool
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(leap.common.events.events_pb2.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int

    :return: the response from server for synch calls or nothing for asynch
        calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    return client.register(signal, callback, uid, replace, reqcbk, timeout)


def unregister(signal, uid=None, reqcbk=None, timeout=1000):
    """
    Unregister a callback.

    If C{uid} is specified, unregisters only the callback identified by that
    unique id. Otherwise, unregisters all callbacks registered for C{signal}.

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
             calls.
    :rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    return client.unregister(signal, uid, reqcbk, timeout)


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
    :param mac_method: the method used to auth mac
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
    return client.signal(signal, content, mac_method, mac, reqcbk, timeout)

def ping_client(port, reqcbk=None, timeout=1000):
    """
    Ping a client running in C{port}.

    :param port: the port in which the client should be listening
    :type port: int
    :param reqcbk: a callback to be called when a response from client is
                   received
    :type reqcbk: function(proto.PingRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int
    """
    return client.ping(port, reqcbk=reqcbk, timeout=timeout)


def ping_server(port=server.SERVER_PORT, reqcbk=None, timeout=1000):
    """
    Ping the server.

    :param port: the port in which server should be listening
    :type port: int
    :param reqcbk: a callback to be called when a response from server is
                   received
    :type reqcbk: function(proto.PingRequest, proto.EventResponse)
    :param timeout: the timeout for synch calls
    :type timeout: int
    """
    return server.ping(port, reqcbk=reqcbk, timeout=timeout)
