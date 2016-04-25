# -*- coding: utf-8 -*-
# client.py
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
The client end point of the events mechanism.

Clients are the communicating parties of the events mechanism. They
communicate by sending messages to a server, which in turn redistributes
messages to other clients.

When a client registers a callback for a given event, it also tells the
server that it wants to be notified whenever events of that type are sent by
some other client.
"""
import logging
import collections
import uuid
import threading
import time
import pickle
import os

from abc import ABCMeta
from abc import abstractmethod

import zmq
from zmq.eventloop import zmqstream
from zmq.eventloop import ioloop

# XXX some distros don't package libsodium, so we have to be prepared for
#     absence of zmq.auth
try:
    import zmq.auth
except ImportError:
    pass

from leap.common.config import flags, get_path_prefix
from leap.common.zmq_utils import zmq_has_curve
from leap.common.zmq_utils import maybe_create_and_get_certificates
from leap.common.zmq_utils import PUBLIC_KEYS_PREFIX

from leap.common.events.errors import CallbackAlreadyRegisteredError
from leap.common.events.server import EMIT_ADDR
from leap.common.events.server import REG_ADDR
from leap.common.events import catalog


logger = logging.getLogger(__name__)


_emit_addr = EMIT_ADDR
_reg_addr = REG_ADDR
_factory = None
_enable_curve = True


def configure_client(emit_addr, reg_addr, factory=None, enable_curve=True):
    global _emit_addr, _reg_addr, _factory, _enable_curve
    logger.debug("Configuring client with addresses: (%s, %s)" %
                 (emit_addr, reg_addr))
    _emit_addr = emit_addr
    _reg_addr = reg_addr
    _factory = factory
    _enable_curve = enable_curve


class EventsClient(object):
    """
    A singleton client for the events mechanism.
    """

    __metaclass__ = ABCMeta

    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, emit_addr, reg_addr):
        """
        Initialize the events client.
        """
        logger.debug("Creating client instance.")
        self._callbacks = collections.defaultdict(dict)
        self._emit_addr = emit_addr
        self._reg_addr = reg_addr

    @property
    def callbacks(self):
        return self._callbacks

    @classmethod
    def instance(cls):
        """
        Return a singleton EventsClient instance.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(
                    _emit_addr, _reg_addr, factory=_factory,
                    enable_curve=_enable_curve)
        return cls._instance

    def register(self, event, callback, uid=None, replace=False):
        """
        Register a callback to be executed when an event is received.

        :param event: The event that triggers the callback.
        :type event: Event
        :param callback: The callback to be executed.
        :type callback: callable(event, *content)
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
        logger.debug("Subscribing to event: %s" % event)
        if not uid:
            uid = uuid.uuid4()
        elif uid in self._callbacks[event] and not replace:
            raise CallbackAlreadyRegisteredError()
        self._callbacks[event][uid] = callback
        self._subscribe(str(event))
        return uid

    def unregister(self, event, uid=None):
        """
        Unregister callbacks for an event.

        If uid is not None, then only the callback identified by the given uid
        is removed. Otherwise, all callbacks for the event are removed.

        :param event: The event that triggers the callback.
        :type event: Event
        :param uid: The callback uid.
        :type uid: str
        """
        if not uid:
            logger.debug(
                "Unregistering all callbacks from event %s." % event)
            self._callbacks[event] = {}
        else:
            logger.debug(
                "Unregistering callback %s from event %s." % (uid, event))
            if uid in self._callbacks[event]:
                del self._callbacks[event][uid]
        if not self._callbacks[event]:
            del self._callbacks[event]
            self._unsubscribe(str(event))

    def emit(self, event, *content):
        """
        Send an event.

        :param event: The event to be sent.
        :type event: Event
        :param content: The content of the event.
        :type content: list
        """
        logger.debug("Emitting event: (%s, %s)" % (event, content))
        payload = str(event) + b'\0' + pickle.dumps(content)
        self._send(payload)

    def _handle_event(self, event, content):
        """
        Handle an incoming event.

        :param event: The event to be sent.
        :type event: Event
        :param content: The content of the event.
        :type content: list
        """
        logger.debug("Handling event %s..." % event)
        for uid in self._callbacks[event]:
            callback = self._callbacks[event][uid]
            logger.debug("Executing callback %s." % uid)
            self._run_callback(callback, event, content)

    @abstractmethod
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
        pass

    @abstractmethod
    def _subscribe(self, tag):
        """
        Subscribe to a tag on the zmq SUB socket.

        :param tag: The tag to be subscribed.
        :type tag: str
        """
        pass

    @abstractmethod
    def _unsubscribe(self, tag):
        """
        Unsubscribe from a tag on the zmq SUB socket.

        :param tag: The tag to be unsubscribed.
        :type tag: str
        """
        pass

    @abstractmethod
    def _send(self, data):
        """
        Send data through PUSH socket.

        :param data: The data to be sent.
        :type event: str
        """
        pass

    def shutdown(self):
        self.__class__.reset()

    @classmethod
    def reset(cls):
        with cls._instance_lock:
            cls._instance = None


class EventsIOLoop(ioloop.ZMQIOLoop):
    """
    An extension of zmq's ioloop that can wait until there are no callbacks
    in the queue before stopping.
    """

    def stop(self, wait=False):
        """
        Stop the I/O loop.

        :param wait: Whether we should wait for callbacks in queue to finish
                     before stopping.
        :type wait: bool
        """
        if wait:
            # prevent new callbacks from being added
            with self._callback_lock:
                self._closing = True
            # wait until all callbacks have been executed
            while self._callbacks:
                time.sleep(0.1)
        ioloop.ZMQIOLoop.stop(self)


class EventsClientThread(threading.Thread, EventsClient):
    """
    A threaded version of the events client.
    """

    def __init__(self, emit_addr, reg_addr, factory=None, enable_curve=True):
        """
        Initialize the events client.
        """
        threading.Thread.__init__(self)
        EventsClient.__init__(self, emit_addr, reg_addr)
        self._lock = threading.Lock()
        self._initialized = threading.Event()
        self._config_prefix = os.path.join(
            get_path_prefix(flags.STANDALONE), "leap", "events")
        self._loop = None
        self._factory = factory
        self._context = None
        self._push = None
        self._sub = None

        if enable_curve:
            self.use_curve = zmq_has_curve()
        else:
            self.use_curve = False

    def _init_zmq(self):
        """
        Initialize ZMQ connections.
        """
        self._loop = EventsIOLoop()
        # we need a new context for each thread
        self._context = zmq.Context()
        # connect SUB first, otherwise we might miss some event sent from this
        # same client
        self._sub = self._zmq_connect_sub()
        self._push = self._zmq_connect_push()

    def _zmq_connect(self, socktype, address):
        """
        Connect to an address using with a zmq socktype.

        :param socktype: The ZMQ socket type.
        :type socktype: int
        :param address: The address to connect to.
        :type address: str

        :return: A ZMQ connection stream.
        :rtype: ZMQStream
        """
        logger.debug("Connecting %s to %s." % (socktype, address))
        socket = self._context.socket(socktype)
        # configure curve authentication
        if self.use_curve:
            public, private = maybe_create_and_get_certificates(
                self._config_prefix, "client")
            server_public_file = os.path.join(
                self._config_prefix, PUBLIC_KEYS_PREFIX, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            socket.curve_publickey = public
            socket.curve_secretkey = private
            socket.curve_serverkey = server_public
        stream = zmqstream.ZMQStream(socket, self._loop)
        socket.connect(address)
        return stream

    def _zmq_connect_push(self):
        """
        Initialize the client's PUSH connection.

        :return: A ZMQ connection stream.
        :rtype: ZMQStream
        """
        return self._zmq_connect(zmq.PUSH, self._emit_addr)

    def _zmq_connect_sub(self):
        """
        Initialize the client's SUB connection.

        :return: A ZMQ connection stream.
        :rtype: ZMQStream
        """
        stream = self._zmq_connect(zmq.SUB, self._reg_addr)
        stream.on_recv(self._on_recv)
        return stream

    def _on_recv(self, msg):
        """
        Handle an incoming message in the SUB socket.

        :param msg: The received message.
        :type msg: str
        """
        ev_str, content_pickle = msg[0].split(b'\0', 1)  # undo txzmq tagging
        event = getattr(catalog, ev_str)
        content = pickle.loads(content_pickle)
        self._handle_event(event, content)

    def _subscribe(self, tag):
        """
        Subscribe from a tag on the zmq SUB socket.

        :param tag: The tag to be subscribed.
        :type tag: str
        """
        self._sub.socket.setsockopt(zmq.SUBSCRIBE, tag)

    def _unsubscribe(self, tag):
        """
        Unsubscribe from a tag on the zmq SUB socket.

        :param tag: The tag to be unsubscribed.
        :type tag: str
        """
        self._sub.socket.setsockopt(zmq.UNSUBSCRIBE, tag)

    def _send(self, data):
        """
        Send data through PUSH socket.

        :param data: The data to be sent.
        :type event: str
        """
        # add send() as a callback for ioloop so it works between threads
        self._loop.add_callback(lambda: self._push.send(data))

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
        self._loop.add_callback(lambda: callback(event, *content))

    def register(self, event, callback, uid=None, replace=False):
        """
        Register a callback to be executed when an event is received.

        :param event: The event that triggers the callback.
        :type event: Event
        :param callback: The callback to be executed.
        :type callback: callable(event, *content)
        :param uid: The callback uid.
        :type uid: str
        :param replace: Wether an eventual callback with same ID should be
                        replaced.
        :type replace: bool

        :return: The callback uid.
        :rtype: str

        :raises CallbackAlreadyRegisteredError: when there's already a
                callback identified by the given uid and replace is False.
        """
        self.ensure_client()
        return EventsClient.register(
            self, event, callback, uid=uid, replace=replace)

    def unregister(self, event, uid=None):
        """
        Unregister callbacks for an event.

        If uid is not None, then only the callback identified by the given uid
        is removed. Otherwise, all callbacks for the event are removed.

        :param event: The event that triggers the callback.
        :type event: Event
        :param uid: The callback uid.
        :type uid: str
        """
        self.ensure_client()
        EventsClient.unregister(self, event, uid=uid)

    def emit(self, event, *content):
        """
        Send an event.

        :param event: The event to be sent.
        :type event: Event
        :param content: The content of the event.
        :type content: list
        """
        self.ensure_client()
        EventsClient.emit(self, event, *content)

    def run(self):
        """
        Run the events client.
        """
        logger.debug("Starting ioloop.")
        self._init_zmq()
        self._initialized.set()
        self._loop.start()
        self._loop.close()
        logger.debug("Ioloop finished.")

    def ensure_client(self):
        """
        Make sure the events client thread is started.
        """
        with self._lock:
            if not self.is_alive():
                self.daemon = True
                self.start()
                self._initialized.wait()

    def shutdown(self):
        """
        Shutdown the events client thread.
        """
        logger.debug("Shutting down client...")
        with self._lock:
            if self.is_alive():
                self._loop.stop(wait=True)
        EventsClient.shutdown(self)


def shutdown():
    """
    Shutdown the events client thread.
    """
    EventsClientThread.instance().shutdown()


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
    return EventsClientThread.instance().register(
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
    return EventsClientThread.instance().unregister(event, uid=uid)


def emit(event, *content):
    """
    Send an event.

    :param event: The event to be sent.
    :type event: str
    :param content: The content of the event.
    :type content: list
    """
    return EventsClientThread.instance().emit(event, *content)


def instance():
    """
    Return an instance of the events client.

    :return: An instance of the events client.
    :rtype: EventsClientThread
    """
    return EventsClientThread.instance()
