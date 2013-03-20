import unittest
from protobuf.socketrpc import RpcService
from leap.common import events
from leap.common.events import service
from leap.common.events.signal_pb2 import (
    SignalRequest,
    SignalService,
    SignalService_Stub,
)


port = 8090

class EventsTestCase(unittest.TestCase):

    def _start_service(self):
        return service.SignalServiceThread.start_service(port)

    def setUp(self):
        super(EventsTestCase, self).setUp()
        self._service = self._start_service()

    def tearDown(self):
        events.registered_callbacks = {}
        super(EventsTestCase, self).tearDown()

    def test_service_singleton(self):
        self.assertTrue(self._service.get_instance() == self._service,
                        "Can't get singleton class for service.")

    def test_register_signal(self):
        key = SignalRequest.SOLEDAD_CREATING_KEYS
        self.assertEqual({}, events.registered_callbacks,
                        'There should be no registered_callbacks events when '
                        'service has just started.')
        events.register(key, lambda x: True)
        self.assertEqual(1, len(events.registered_callbacks),
                         'Wrong number of registered callbacks.')
        self.assertEqual(events.registered_callbacks.keys(), [key],
                         'Couldn\'t locate registered signal.')
        events.register(key, lambda x: True)
        self.assertEqual(1, len(events.registered_callbacks),
                         'Wrong number of registered callbacks.')
        self.assertEqual(events.registered_callbacks.keys(), [key],
                         'Couldn\'t locate registered signal.')
        self.assertEqual(
            2,
            len(events.registered_callbacks[SignalRequest.SOLEDAD_CREATING_KEYS]),
            'Wrong number of registered callbacks.')
        key2 = SignalRequest.CLIENT_UID
        events.register(key2, lambda x: True)
        self.assertEqual(2, len(events.registered_callbacks),
                         'Wrong number of registered callbacks.')
        self.assertEqual(
            sorted(events.registered_callbacks.keys()),
            sorted([key2, key]),
            'Wrong keys in `registered_keys`.')

    def test_register_signal_replace(self):
        key = SignalRequest.SOLEDAD_CREATING_KEYS
        cbk = lambda x: True
        self.assertEqual({}, events.registered_callbacks,
                        'There should be no registered_callbacks events when '
                        'service has just started.')
        events.register(key, cbk, uid=1)
        self.assertRaises(Exception, events.register, key, lambda x: True, uid=1)
        self.assertEquals(1,
                          events.register(key, lambda x: True, uid=1, replace=True),
                          "Could not replace callback.")
        self.assertEqual(1, len(events.registered_callbacks),
                         'Wrong number of registered callbacks.')
        self.assertEqual(events.registered_callbacks.keys(), [key],
                         'Couldn\'t locate registered signal.')

    def test_signal_response_status(self):
        sig = SignalRequest.SOLEDAD_CREATING_KEYS
        cbk = lambda x: True
        events.register(sig, cbk)
        request = SignalRequest()
        request.id = 1
        request.signal = sig
        request.content = 'my signal contents'
        request.mac_method = 'nomac'
        request.mac = ""
        service = RpcService(SignalService_Stub, port, 'localhost')
        response = service.signal(request, timeout=1000)
        self.assertEqual(response.OK, response.status,
                         'Wrong response status.')
