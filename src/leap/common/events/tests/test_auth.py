# -*- coding: utf-8 -*-
# test_zmq_components.py
# Copyright (C) 2014 LEAP
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
Tests for the auth module.
"""
import os

from twisted.trial import unittest
from txzmq import ZmqFactory

from leap.common.events import auth
from leap.common.testing.basetest import BaseLeapTest
from leap.common.zmq_utils import PUBLIC_KEYS_PREFIX
from leap.common.zmq_utils import maybe_create_and_get_certificates

from txzmq.test import _wait


class ZmqAuthTestCase(unittest.TestCase, BaseLeapTest):

    def setUp(self):
        self.setUpEnv(launch_events_server=False)

        self.factory = ZmqFactory()
        self._config_prefix = os.path.join(self.tempdir, "leap", "events")

        self.public, self.secret = maybe_create_and_get_certificates(
            self._config_prefix, 'server')

        self.authenticator = auth.TxAuthenticator(self.factory)
        self.authenticator.start()
        self.auth_req = auth.TxAuthenticationRequest(self.factory)

    def tearDown(self):
        self.factory.shutdown()
        self.tearDownEnv()

    def test_curve_auth(self):
        self.auth_req.start()
        self.auth_req.allow('127.0.0.1')
        public_keys_dir = os.path.join(self._config_prefix, PUBLIC_KEYS_PREFIX)
        self.auth_req.configure_curve(domain="*", location=public_keys_dir)

        def check(ignored):
            authenticator = self.authenticator.authenticator
            certs = authenticator.certs['*']
            self.failUnlessEqual(authenticator.whitelist, set([u'127.0.0.1']))
            self.failUnlessEqual(certs[certs.keys()[0]], True)

        return _wait(0.1).addCallback(check)
