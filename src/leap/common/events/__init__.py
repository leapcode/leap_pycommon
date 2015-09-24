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
This is an events mechanism that uses a server to allow for emitting events
between clients.

Application components should use the interface available in this file to
register callbacks to be executed upon receiving specific events, and to send
events to other components.

To register a callback to be executed when a specific event is emitted, use
leap.common.events.register():

>>> from leap.common.events import register
>>> from leap.common.events import catalog
>>> register(catalog.CLIENT_UID, lambda sig, content: do_something(content))

To emit an event, use leap.common.events.emit():

>>> from leap.common.events import emit
>>> from leap.common.events import catalog
>>> emit(catalog.CLIENT_UID)
"""
import logging
import argparse

from leap.common.events import client
from leap.common.events import txclient
from leap.common.events import server
from leap.common.events import flags
from leap.common.events.flags import set_events_enabled

from leap.common.events import catalog


__all__ = [
    "register",
    "unregister",
    "emit",
    "catalog",
    "set_events_enabled"
]


logger = logging.getLogger(__name__)


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

    :raises CallbackAlreadyRegistered: when there's already a callback
            identified by the given uid and replace is False.
    """
    if flags.EVENTS_ENABLED:
        return client.register(event, callback, uid, replace)


def register_async(event, callback, uid=None, replace=False):
    if flags.EVENTS_ENABLED:
        return txclient.register(event, callback, uid, replace)


def unregister(event, uid=None):
    """
    Unregister callbacks for an event.

    If uid is not None, then only the callback identified by the given uid is
    removed. Otherwise, all callbacks for the event are removed.

    :param event: The event that triggers the callback.
    :type event: Event
    :param uid: The callback uid.
    :type uid: str
    """
    if flags.EVENTS_ENABLED:
        return client.unregister(event, uid)


def unregister_async(event, uid=None):
    if flags.EVENTS_ENABLED:
        return txclient.unregister(event, uid)


def emit(event, *content):
    """
    Send an event.

    :param event: The event to be sent.
    :type event: Event
    :param content: The content of the event.
    :type content: list
    """
    if flags.EVENTS_ENABLED:
        return client.emit(event, *content)


def emit_async(event, *content):
    if flags.EVENTS_ENABLED:
        return txclient.emit(event, *content)


if __name__ == "__main__":

    def _echo(event, *content):
        print "Received event: (%s, %s)" % (event, content)

    def _parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--debug", "-d", action="store_true",
            help="print debug information")

        subparsers = parser.add_subparsers(dest="command")

        # server options
        server_parser = subparsers.add_parser(
            "server", help="Run an events server.")
        server_parser.add_argument(
            "--emit-addr",
            help="The address in which to listen for events",
            default=server.EMIT_ADDR)
        server_parser.add_argument(
            "--reg-addr",
            help="The address in which to listen for registration for events.",
            default=server.REG_ADDR)

        # client options
        client_parser = subparsers.add_parser(
            "client", help="Run an events client.")
        client_parser.add_argument(
            "--emit-addr",
            help="The address in which to emit events.",
            default=server.EMIT_ADDR)
        client_parser.add_argument(
            "--reg-addr",
            help="The address in which to register for events.",
            default=server.REG_ADDR)
        group = client_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--reg', help="register an event")
        group.add_argument('--emit', help="send an event")
        client_parser.add_argument(
            '--content', help="the content of the event", default=None)

        # txclient options
        txclient_parser = subparsers.add_parser(
            "txclient", help="Run an events twisted client.")
        txclient_parser.add_argument(
            "--emit-addr",
            help="The address in which to emit events.",
            default=server.EMIT_ADDR)
        txclient_parser.add_argument(
            "--reg-addr",
            help="The address in which to register for events.",
            default=server.REG_ADDR)
        group = txclient_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--reg', help="register an event")
        group.add_argument('--emit', help="send an event")
        txclient_parser.add_argument(
            '--content', help="the content of the event", default=None)

        return parser.parse_args()

    args = _parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.command == "server":
        # run server
        server.ensure_server(emit_addr=args.emit_addr, reg_addr=args.reg_addr)
        from twisted.internet import reactor
        reactor.run()
    elif args.command == "client":
        if args.reg:
            event = getattr(catalog, args.reg)
            # run client and register to a signal
            register(event, _echo)
            # make sure we stop on CTRL+C
            import signal
            signal.signal(
                signal.SIGINT, lambda sig, frame: client.shutdown())
            # wait until client thread dies
            import time
            while client.EventsClientThread.instance().is_alive():
                time.sleep(0.1)
        if args.emit:
            # run client and emit a signal
            event = getattr(catalog, args.emit)
            emit(event, args.content)
            client.shutdown()
    elif args.command == "txclient":
        from leap.common.events import txclient
        register = txclient.register
        emit = txclient.emit
        if args.reg:
            event = getattr(catalog, args.reg)
            # run client and register to a signal
            register(event, _echo)
            from twisted.internet import reactor
            reactor.run()
        if args.emit:
            # run client and emit a signal
            event = getattr(catalog, args.emit)
            emit(event, args.content)
