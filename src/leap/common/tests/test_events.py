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
import socket
import threading
import random


from mock import Mock
from protobuf.socketrpc import RpcService
from leap.common import events
from leap.common.events import (
    server,
    client,
    mac_auth,
)
from leap.common.events.events_pb2 import (
    EventsServerService,
    EventsServerService_Stub,
    EventsClientService_Stub,
    EventResponse,
    SignalRequest,
    RegisterRequest,
    PingRequest,
    SOLEDAD_CREATING_KEYS,
    CLIENT_UID,
)


port = 8090

received = False


class EventsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        server.EventsServerDaemon.ensure(8090)
        cls.callbacks = events.client.registered_callbacks

    @classmethod
    def tearDownClass(cls):
        # give some time for requests to be processed.
        time.sleep(1)

    def setUp(self):
        super(EventsTestCase, self).setUp()

    def tearDown(self):
        #events.client.registered_callbacks = {}
        server.registered_clients = {}
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

    def test_client_register(self):
        """
        Ensure clients can register callbacks.
        """
        self.assertTrue(1 not in self.callbacks,
                        'There should should be no callback for this signal.')
        events.register(1, lambda x: True)
        self.assertTrue(1 in self.callbacks,
                        'Could not register signal in local client.')
        events.register(2, lambda x: True)
        self.assertTrue(1 in self.callbacks,
                        'Could not register signal in local client.')
        self.assertTrue(2 in self.callbacks,
                        'Could not register signal in local client.')

    def test_register_signal_replace(self):
        """
        Make sure clients can replace already registered callbacks.
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

    def test_signal_executes_callback(self):
        """
        Ensure callback is executed upon receiving signal.
        """
        sig = CLIENT_UID
        request = SignalRequest()
        request.event = sig
        request.content = 'my signal contents'
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')

        # register a callback
        flag = Mock()
        events.register(sig, lambda req: flag(req.event))
        # signal
        response = service.signal(request)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')
        time.sleep(1)  # wait for signal to arrive
        flag.assert_called_once_with(sig)

    def test_events_server_service_register(self):
        """
        Ensure the server can register clients to be signaled.
        """
        sig = 5
        request = RegisterRequest()
        request.event = sig
        request.port = 8091
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        complist = server.registered_clients
        self.assertEqual({}, complist,
                         'There should be no registered_ports when '
                         'server has just been created.')
        response = service.register(request, timeout=1000)
        self.assertTrue(sig in complist, "Signal not registered succesfully.")
        self.assertTrue(8091 in complist[sig],
                        'Failed registering client port.')

    def test_client_request_register(self):
        """
        Ensure clients can register themselves with server.
        """
        sig = 6
        complist = server.registered_clients
        self.assertTrue(sig not in complist,
                        'There should be no registered clients for this '
                        'signal.')
        events.register(sig, lambda x: True)
        time.sleep(0.1)
        port = client.EventsClientDaemon.get_instance().get_port()
        self.assertTrue(sig in complist, 'Failed registering client.')
        self.assertTrue(port in complist[sig],
                        'Failed registering client port.')

    def test_client_receives_signal(self):
        """
        Ensure clients can receive signals.
        """
        sig = 7
        flag = Mock()

        events.register(sig, lambda req: flag(req.event))
        request = SignalRequest()
        request.event = sig
        request.content = ""
        request.mac_method = mac_auth.MacMethod.MAC_NONE
        request.mac = ""
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        response = service.signal(request, timeout=1000)
        self.assertTrue(response is not None, 'Did not receive response.')
        time.sleep(0.5)
        flag.assert_called_once_with(sig)

    def test_client_send_signal(self):
        """
        Ensure clients can send signals.
        """
        sig = 8
        response = events.signal(sig)
        self.assertTrue(response.status == response.OK,
                        'Received wrong response status when signaling.')

    def test_client_unregister_all(self):
        """
        Test that the client can unregister all events for one signal.
        """
        sig = CLIENT_UID
        complist = server.registered_clients
        events.register(sig, lambda x: True)
        events.register(sig, lambda x: True)
        time.sleep(0.1)
        events.unregister(sig)
        time.sleep(0.1)
        port = client.EventsClientDaemon.get_instance().get_port()
        self.assertFalse(bool(complist[sig]))
        self.assertTrue(port not in complist[sig])

    def test_client_unregister_by_uid(self):
        """
        Test that the client can unregister an event by uid.
        """
        sig = CLIENT_UID
        complist = server.registered_clients
        events.register(sig, lambda x: True, uid='cbkuid')
        events.register(sig, lambda x: True, uid='cbkuid2')
        time.sleep(0.1)
        events.unregister(sig, uid='cbkuid')
        time.sleep(0.1)
        port = client.EventsClientDaemon.get_instance().get_port()
        self.assertTrue(sig in complist)
        self.assertTrue(len(complist[sig]) == 1)
        self.assertTrue(
            client.registered_callbacks[sig].pop()[0] == 'cbkuid2')
        self.assertTrue(port in complist[sig])

    def test_server_replies_ping(self):
        """
        Ensure server replies to a ping.
        """
        request = PingRequest()
        service = RpcService(EventsServerService_Stub, port, 'localhost')
        response = service.ping(request, timeout=1000)
        self.assertIsNotNone(response)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_client_replies_ping(self):
        """
        Ensure clients reply to a ping.
        """
        daemon = client.ensure_client_daemon()
        port = daemon.get_port()
        request = PingRequest()
        service = RpcService(EventsClientService_Stub, port, 'localhost')
        response = service.ping(request, timeout=1000)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_server_ping(self):
        """
        Ensure the function from server module pings correctly.
        """
        response = server.ping()
        self.assertIsNotNone(response)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_client_ping(self):
        """
        Ensure the function from client module pings correctly.
        """
        daemon = client.ensure_client_daemon()
        response = client.ping(daemon.get_port())
        self.assertIsNotNone(response)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_module_ping_server(self):
        """
        Ensure the function from main module pings server correctly.
        """
        response = events.ping_server()
        self.assertIsNotNone(response)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_module_ping_client(self):
        """
        Ensure the function from main module pings clients correctly.
        """
        daemon = client.ensure_client_daemon()
        response = events.ping_client(daemon.get_port())
        self.assertIsNotNone(response)
        self.assertEqual(EventResponse.OK, response.status,
                         'Wrong response status.')

    def test_ensure_server_raises_if_port_taken(self):
        """
        Verify that server raises an exception if port is already taken.
        """
        # get a random free port
        while True:
            port = random.randint(1024, 65535)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('localhost', port))
                s.close()
            except:
                break

        class PortBlocker(threading.Thread):

            def run(self):
                conns = 0
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('localhost', port))
                s.setblocking(1)
                s.listen(1)
                while conns < 2:  # blocks until rece
                    conns += 1
                    s.accept()
                s.close()

        # block the port
        taker = PortBlocker()
        taker.start()
        time.sleep(1)  # wait for thread to start.
        self.assertRaises(
            server.PortAlreadyTaken, server.ensure_server, port)

    def test_async_register(self):
        """
        Test asynchronous registering of callbacks.
        """
        flag = Mock()

        # executed after async register, when response is received from server
        def reqcbk(request, response):
            flag(request.event, response.status)

        # callback registered by application
        def callback(request):
            pass

        # passing a callback as reqcbk param makes the call asynchronous
        result = events.register(CLIENT_UID, callback, reqcbk=reqcbk)
        self.assertIsNone(result)
        events.signal(CLIENT_UID)
        time.sleep(1)  # wait for signal to arrive from server
        flag.assert_called_once_with(CLIENT_UID, EventResponse.OK)

    def test_async_signal(self):
        """
        Test asynchronous registering of callbacks.
        """
        flag = Mock()

        # executed after async signal, when response is received from server
        def reqcbk(request, response):
            flag(request.event, response.status)

        # passing a callback as reqcbk param makes the call asynchronous
        result = events.signal(CLIENT_UID, reqcbk=reqcbk)
        self.assertIsNone(result)
        time.sleep(1)  # wait for signal to arrive from server
        flag.assert_called_once_with(CLIENT_UID, EventResponse.OK)

    def test_async_unregister(self):
        """
        Test asynchronous unregistering of callbacks.
        """
        flag = Mock()

        # executed after async signal, when response is received from server
        def reqcbk(request, response):
            flag(request.event, response.status)

        # callback registered by application
        def callback(request):
            pass

        # passing a callback as reqcbk param makes the call asynchronous
        events.register(CLIENT_UID, callback)
        result = events.unregister(CLIENT_UID, reqcbk=reqcbk)
        self.assertIsNone(result)
        time.sleep(1)  # wait for signal to arrive from server
        flag.assert_called_once_with(CLIENT_UID, EventResponse.OK)

    def test_async_ping_server(self):
        """
        Test asynchronous pinging of server.
        """
        flag = Mock()

        # executed after async signal, when response is received from server
        def reqcbk(request, response):
            flag(response.status)

        result = events.ping_server(reqcbk=reqcbk)
        self.assertIsNone(result)
        time.sleep(1)  # wait for response to arrive from server.
        flag.assert_called_once_with(EventResponse.OK)

    def test_async_ping_client(self):
        """
        Test asynchronous pinging of client.
        """
        flag = Mock()

        # executed after async signal, when response is received from server
        def reqcbk(request, response):
            flag(response.status)

        daemon = client.ensure_client_daemon()
        result = events.ping_client(daemon.get_port(), reqcbk=reqcbk)
        self.assertIsNone(result)
        time.sleep(1)  # wait for response to arrive from server.
        flag.assert_called_once_with(EventResponse.OK)
