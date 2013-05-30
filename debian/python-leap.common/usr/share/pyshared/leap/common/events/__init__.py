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
An events mechanism that allows for signaling of events between components.
"""

import logging
import socket


from leap.common.events import (
    events_pb2,
    server,
    component,
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

    @param signal: the signal that causes the callback to be launched
    @type signal: int (see the `events.proto` file)
    @param callback: the callback to be called when the signal is received
    @type callback: function
    @param uid: a unique id for the callback
    @type uid: int
    @param replace: should an existent callback with same uid be replaced?
    @type replace: bool
    @param reqcbk: a callback to be called when a response from server is
        received
    @type reqcbk: function
        callback(leap.common.events.events_pb2.EventResponse)
    @param timeout: the timeout for synch calls
    @type timeout: int

    @return: the response from server for synch calls or nothing for asynch
        calls
    @rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    return component.register(signal, callback, uid, replace, reqcbk, timeout)


def signal(signal, content="", mac_method="", mac="", reqcbk=None,
           timeout=1000):
    """
    Send `signal` event to events server.

    Will timeout after timeout ms if response has not been received. The
    timeout arg is only used for asynch requests.  If a reqcbk callback has
    been supplied the timeout arg is not used. The response value will be
    returned for a synch request but nothing will be returned for an asynch
    request.

    @param signal: the signal that causes the callback to be launched
    @type signal: int (see the `events.proto` file)
    @param content: the contents of the event signal
    @type content: str
    @param mac_method: the method used to auth mac
    @type mac_method: str
    @param mac: the content of the auth mac
    @type mac: str
    @param reqcbk: a callback to be called when a response from server is
        received
    @type reqcbk: function
        callback(leap.common.events.events_pb2.EventResponse)
    @param timeout: the timeout for synch calls
    @type timeout: int

    @return: the response from server for synch calls or nothing for asynch
        calls
    @rtype: leap.common.events.events_pb2.EventsResponse or None
    """
    return component.signal(signal, content, mac_method, mac, reqcbk, timeout)
