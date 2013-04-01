## -*- coding: utf-8 -*-
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

import unittest
import sets
import time
from protobuf.socketrpc import RpcService
from leap.common import events
from leap.common.events import (
    server,
    component,
    mac_auth,
)
from leap.common.events.events_pb2 import (
    EventsServerService,
    EventsServerService_Stub,
    EventResponse,
    SignalRequest,
    RegisterRequest,
    SOLEDAD_CREATING_KEYS,
    CLIENT_UID,
)


port = 8090

received = False
local_callback_executed = False


def callback(request, reponse):
    return True


class EventsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        server.EventsServerDaemon.ensure(8090)
        cls.callbacks = events.component.registered_callbacks

    @classmethod
    def tearDownClass(cls):
        # give some time for requests to be processed.
        time.sleep(1)

    def setUp(self):
        super(EventsTestCase, self).setUp()

    def tearDown(self):
        #events.component.registered_callbacks = {}
        server.registered_components = {}
        super(EventsTestCase, self).tearDown()

    def test_service_singleton(self):
        """
        Ensure that there's always just one instance of the server daemon
        running.
        """
        service1 = server.EventsServerDaemon.ensure(8090)
        service2 = server.EventsServerDaemon.ensure(8090)
        self.assertEqual(service1, service2,
                         "Can't get singleton class for service.")

    def test_component_register(self):
        """
        Ensure components can register callbacks.
        """
        self.assertTrue(1 not in self.callbacks,
                        'There should should be no callback for this signal.')
        events.register(1, lambda x: True)
        self.assertTrue(1 in self.callbacks,
                        'Could not register signal in local component.')
        events.register(2, lambda x: True)
        self.assertTrue(1 in self.callbacks,
                        'Could not register signal in local component.')
        self.assertTrue(2 in self.callbacks,
                        'Could not register signal in local component.')

    def test_register_signal_replace(self):
        """
        Make sure components can replace already registered callbacks.
        """
        sig = 3
        cbk = lambda x: True
        events.register(sig, cbk, uid=1)
        self.assertRaises(Exception, events.register, sig, lambda x: True,
                          uid=1)
        events.register(sig, lambda x: True, uid=1, replace=True)
        self.assertTrue(sig in self.callbacks, 'Could not register signal.')
        self.assertEqual(1, len(self.callbacks[sig]),
                         'Wrong number of registered callbacks.')

    def test_signal_response_status(self):
        """
        Ensure there's an appropriate response from server when signaling.
        """
        sig = 4
        request = SignalRequest()
        request.event = sig
        request.content = 'my signal contents'
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        # test synch
        response = service.signal(request, timeout=1000)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')
        # test asynch

        def local_callback(request, response):
            global local_callback_executed
            local_callback_executed = True

        events.register(sig, local_callback)
        service.signal(request, callback=local_callback)
        time.sleep(0.1)
        self.assertTrue(local_callback_executed,
                        'Local callback did not execute.')

    def test_events_server_service_register(self):
        """
        Ensure the server can register components to be signaled.
        """
        sig = 5
        request = RegisterRequest()
        request.event = sig
        request.port = 8091
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        complist = server.registered_components
        self.assertEqual({}, complist,
                         'There should be no registered_ports when '
                         'server has just been created.')
        response = service.register(request, timeout=1000)
        self.assertTrue(sig in complist, "Signal not registered succesfully.")
        self.assertTrue(8091 in complist[sig],
                        'Failed registering component port.')

    def test_component_request_register(self):
        """
        Ensure components can register themselves with server.
        """
        sig = 6
        complist = server.registered_components
        self.assertTrue(sig not in complist,
                        'There should be no registered components for this '
                        'signal.')
        events.register(sig, lambda x: True)
        time.sleep(0.1)
        port = component.EventsComponentDaemon.get_instance().get_port()
        self.assertTrue(sig in complist, 'Failed registering component.')
        self.assertTrue(port in complist[sig],
                        'Failed registering component port.')

    def test_component_receives_signal(self):
        """
        Ensure components can receive signals.
        """
        sig = 7

        def getsig(param=None):
            global received
            received = True

        events.register(sig, getsig)
        request = SignalRequest()
        request.event = sig
        request.content = ""
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        response = service.signal(request, timeout=1000)
        self.assertTrue(response is not None, 'Did not receive response.')
        time.sleep(0.5)
        self.assertTrue(received, 'Did not receive signal back.')

    def test_component_send_signal(self):
        """
        Ensure components can send signals.
        """
        sig = 8
        response = events.signal(sig)
        self.assertTrue(response.status == response.OK,
                        'Received wrong response status when signaling.')
