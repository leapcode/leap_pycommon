# -*- coding: utf-8 -*-
# test_events.py
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
Tests for the events framework
"""
import os
import logging

from twisted.internet.reactor import callFromThread
from twisted.trial import unittest
from twisted.internet import defer

from txzmq import ZmqFactory

from leap.common.events import server
from leap.common.events import client
from leap.common.events import flags
from leap.common.events import txclient
from leap.common.events import catalog
from leap.common.events.errors import CallbackAlreadyRegisteredError


if 'DEBUG' in os.environ:
    logging.basicConfig(level=logging.DEBUG)


class EventsGenericClientTestCase(object):

    def setUp(self):
        flags.set_events_enabled(True)
        self.factory = ZmqFactory()
        self._server = server.ensure_server(
            emit_addr="tcp://127.0.0.1:0",
            reg_addr="tcp://127.0.0.1:0",
            factory=self.factory,
            enable_curve=False)

        self._client.configure_client(
            emit_addr="tcp://127.0.0.1:%d" % self._server.pull_port,
            reg_addr="tcp://127.0.0.1:%d" % self._server.pub_port,
            factory=self.factory, enable_curve=False)

    def tearDown(self):
        flags.set_events_enabled(False)
        self.factory.shutdown()
        self._client.instance().reset()

    def test_client_register(self):
        """
        Ensure clients can register callbacks.
        """
        callbacks = self._client.instance().callbacks
        self.assertTrue(len(callbacks) == 0,
                        'There should be no callback for this event.')
        # register one event
        event1 = catalog.CLIENT_UID

        def cbk1(event, _):
            return True

        uid1 = self._client.register(event1, cbk1)
        # assert for correct registration
        self.assertTrue(len(callbacks) == 1)
        self.assertTrue(callbacks[event1][uid1] == cbk1,
                        'Could not register event in local client.')
        # register another event
        event2 = catalog.CLIENT_SESSION_ID

        def cbk2(event, _):
            return True

        uid2 = self._client.register(event2, cbk2)
        # assert for correct registration
        self.assertTrue(len(callbacks) == 2)
        self.assertTrue(callbacks[event2][uid2] == cbk2,
                        'Could not register event in local client.')

    def test_register_signal_replace(self):
        """
        Make sure clients can replace already registered callbacks.
        """
        event = catalog.CLIENT_UID
        d = defer.Deferred()

        def cbk_fail(event, _):
            return callFromThread(d.errback, event)

        def cbk_succeed(event, _):
            return callFromThread(d.callback, event)

        self._client.register(event, cbk_fail, uid=1)
        self._client.register(event, cbk_succeed, uid=1, replace=True)
        self._client.emit(event, None)
        return d

    def test_register_signal_replace_fails_when_replace_is_false(self):
        """
        Make sure clients trying to replace already registered callbacks fail
        when replace=False
        """
        event = catalog.CLIENT_UID
        self._client.register(event, lambda event, _: None, uid=1)
        self.assertRaises(
            CallbackAlreadyRegisteredError,
            self._client.register,
            event, lambda event, _: None, uid=1, replace=False)

    def test_register_more_than_one_callback_works(self):
        """
        Make sure clients can replace already registered callbacks.
        """
        event = catalog.CLIENT_UID
        d1 = defer.Deferred()

        def cbk1(event, _):
            return callFromThread(d1.callback, event)

        d2 = defer.Deferred()

        def cbk2(event, _):
            return d2.callback(event)

        self._client.register(event, cbk1)
        self._client.register(event, cbk2)
        self._client.emit(event, None)
        d = defer.gatherResults([d1, d2])
        return d

    def test_client_receives_signal(self):
        """
        Ensure clients can receive signals.
        """
        event = catalog.CLIENT_UID
        d = defer.Deferred()

        def cbk(events, _):
            callFromThread(d.callback, event)

        self._client.register(event, cbk)
        self._client.emit(event, None)
        return d

    def test_client_unregister_all(self):
        """
        Test that the client can unregister all events for one signal.
        """
        event1 = catalog.CLIENT_UID
        d = defer.Deferred()
        # register more than one callback for the same event
        self._client.register(
            event1, lambda ev, _: callFromThread(d.errback, None))
        self._client.register(
            event1, lambda ev, _: callFromThread(d.errback, None))
        # unregister and emit the event
        self._client.unregister(event1)
        self._client.emit(event1, None)
        # register and emit another event so the deferred can succeed
        event2 = catalog.CLIENT_SESSION_ID
        self._client.register(
            event2, lambda ev, _: callFromThread(d.callback, None))
        self._client.emit(event2, None)
        return d

    def test_client_unregister_by_uid(self):
        """
        Test that the client can unregister an event by uid.
        """
        event = catalog.CLIENT_UID
        d = defer.Deferred()
        # register one callback that would fail
        uid = self._client.register(
            event, lambda ev, _: callFromThread(d.errback, None))
        # register one callback that will succeed
        self._client.register(
            event, lambda ev, _: callFromThread(d.callback, None))
        # unregister by uid and emit the event
        self._client.unregister(event, uid=uid)
        self._client.emit(event, None)
        return d


class EventsTxClientTestCase(EventsGenericClientTestCase, unittest.TestCase):

    _client = txclient


class EventsClientTestCase(EventsGenericClientTestCase, unittest.TestCase):

    _client = client
