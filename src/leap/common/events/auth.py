# -*- coding: utf-8 -*-
# auth.py
# Copyright (C) 2016 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
ZAP authentication, twisted style.
"""
from zmq import PAIR
from zmq.auth.base import Authenticator, VERSION
from txzmq.connection import ZmqConnection
from zmq.utils.strtypes import b, u

from twisted.python import log

from txzmq.connection import ZmqEndpoint, ZmqEndpointType


class TxAuthenticator(ZmqConnection):

    """
    This does not implement the whole ZAP protocol, but the bare minimum that
    we need.
    """

    socketType = PAIR
    address = 'inproc://zeromq.zap.01'
    encoding = 'utf-8'

    def __init__(self, factory, *args, **kw):
        super(TxAuthenticator, self).__init__(factory, *args, **kw)
        self.authenticator = Authenticator(factory.context)
        self.authenticator._send_zap_reply = self._send_zap_reply

    def start(self):
        endpoint = ZmqEndpoint(ZmqEndpointType.bind, self.address)
        self.addEndpoints([endpoint])

    def messageReceived(self, msg):

        command = msg[0]

        if command == b'ALLOW':
            addresses = [u(m, self.encoding) for m in msg[1:]]
            try:
                self.authenticator.allow(*addresses)
            except Exception as e:
                log.err("Failed to allow %s", addresses)

        elif command == b'CURVE':
            domain = u(msg[1], self.encoding)
            location = u(msg[2], self.encoding)
            self.authenticator.configure_curve(domain, location)

    def _send_zap_reply(self, request_id, status_code, status_text,
                        user_id='user'):
        """
        Send a ZAP reply to finish the authentication.
        """
        user_id = user_id if status_code == b'200' else b''
        if isinstance(user_id, unicode):
            user_id = user_id.encode(self.encoding, 'replace')
        metadata = b''  # not currently used
        reply = [VERSION, request_id, status_code, status_text,
                 user_id, metadata]
        self.send(reply)

    def shutdown(self):
        if self.factory:
            super(TxAuthenticator, self).shutdown()


class TxAuthenticationRequest(ZmqConnection):

    socketType = PAIR
    address = 'inproc://zeromq.zap.01'
    encoding = 'utf-8'

    def start(self):
        endpoint = ZmqEndpoint(ZmqEndpointType.connect, self.address)
        self.addEndpoints([endpoint])

    def allow(self, *addresses):
        self.send([b'ALLOW'] + [b(a, self.encoding) for a in addresses])

    def configure_curve(self, domain='*', location=''):
        domain = b(domain, self.encoding)
        location = b(location, self.encoding)
        self.send([b'CURVE', domain, location])
