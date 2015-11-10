# -*- coding: utf-8 -*-
# http.py
# Copyright (C) 2015 LEAP
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
Twisted HTTP/HTTPS client.
"""

try:
    import twisted
    assert twisted
except ImportError:
    print "*******"
    print "Twisted is needed to use leap.common.http module"
    print ""
    print "Install the extra requirement of the package:"
    print "$ pip install leap.common[Twisted]"
    import sys
    sys.exit(1)


from leap.common.certs import get_compatible_ssl_context_factory
from leap.common.check import leap_assert

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet import defer
from twisted.python import failure

from twisted.web.client import Agent
from twisted.web.client import HTTPConnectionPool
from twisted.web.client import _HTTP11ClientFactory as HTTP11ClientFactory
from twisted.web.client import readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.web._newclient import HTTP11ClientProtocol


__all__ = ["HTTPClient"]


# A default HTTP timeout is used for 2 distinct purposes:
#   1. as HTTP connection timeout, prior to connection estabilshment.
#   2. as data reception timeout, after the connection has been established.
DEFAULT_HTTP_TIMEOUT = 30  # seconds


class _HTTP11ClientFactory(HTTP11ClientFactory):
    """
    A timeout-able HTTP 1.1 client protocol factory.
    """

    def __init__(self, quiescentCallback, timeout):
        """
        :param quiescentCallback: The quiescent callback to be passed to
                                  protocol instances, used to return them to
                                  the connection pool.
        :type quiescentCallback: callable(Protocol)
        :param timeout: The timeout, in seconds, for requests made by
                        protocols created by this factory.
        :type timeout: float
        """
        HTTP11ClientFactory.__init__(self, quiescentCallback)
        self._timeout = timeout

    def buildProtocol(self, _):
        """
        Build the HTTP 1.1 client protocol.
        """
        return _HTTP11ClientProtocol(self._quiescentCallback, self._timeout)


class _HTTPConnectionPool(HTTPConnectionPool):
    """
    A timeout-able HTTP connection pool.
    """

    _factory = _HTTP11ClientFactory

    def __init__(self, reactor, persistent, timeout, maxPersistentPerHost=10):
        HTTPConnectionPool.__init__(self, reactor, persistent=persistent)
        self.maxPersistentPerHost = maxPersistentPerHost
        self._timeout = timeout

    def _newConnection(self, key, endpoint):
        def quiescentCallback(protocol):
            self._putConnection(key, protocol)
        factory = self._factory(quiescentCallback, timeout=self._timeout)
        return endpoint.connect(factory)


class HTTPClient(object):
    """
    HTTP client done the twisted way, with a main focus on pinning the SSL
    certificate.

    By default, it uses a shared connection pool. If you want a dedicated
    one, create and pass on __init__ pool parameter.
    Please note that this client will limit the maximum amount of connections
    by using a DeferredSemaphore.
    This limit is equal to the maxPersistentPerHost used on pool and is needed
    in order to avoid resource abuse on huge requests batches.
    """

    _pool = _HTTPConnectionPool(
        reactor,
        persistent=True,
        timeout=DEFAULT_HTTP_TIMEOUT,
        maxPersistentPerHost=10
    )

    def __init__(self, cert_file=None,
                 timeout=DEFAULT_HTTP_TIMEOUT, pool=None):
        """
        Init the HTTP client

        :param cert_file: The path to the certificate file, if None given the
                          system's CAs will be used.
        :type cert_file: str
        :param timeout: The amount of time that this Agent will wait for the
                        peer to accept a connection and for each request to be
                        finished. If a pool is passed, then this argument is
                        ignored.
        :type timeout: float
        """

        self._timeout = timeout
        self._pool = pool if pool is not None else self._pool
        self._agent = Agent(
            reactor,
            get_compatible_ssl_context_factory(cert_file),
            pool=self._pool,
            connectTimeout=self._timeout)
        self._semaphore = defer.DeferredSemaphore(
            self._pool.maxPersistentPerHost)

    def _createPool(self, maxPersistentPerHost=10, persistent=True):
        pool = _HTTPConnectionPool(reactor, persistent, self._timeout)
        pool.maxPersistentPerHost = maxPersistentPerHost
        return pool

    def _request(self, url, method, body, headers, callback):
        """
        Perform an HTTP request.

        :param url: The URL for the request.
        :type url: str
        :param method: The HTTP method of the request.
        :type method: str
        :param body: The body of the request, if any.
        :type body: str
        :param headers: The headers of the request.
        :type headers: dict
        :param callback: A callback to be added to the request's deferred
                         callback chain.
        :type callback: callable

        :return: A deferred that fires with the body of the request.
        :rtype: twisted.internet.defer.Deferred
        """
        if body:
            body = _StringBodyProducer(body)
        d = self._agent.request(
            method, url, headers=Headers(headers), bodyProducer=body)
        d.addCallback(callback)
        return d

    def request(self, url, method='GET', body=None, headers={},
                callback=readBody):
        """
        Perform an HTTP request, but limit the maximum amount of concurrent
        connections.

        May be passed a callback to be added to the request's deferred
        callback chain. The callback is expected to receive the response of
        the request and may do whatever it wants with the response. By
        default, if no callback is passed, we will use a simple body reader
        which returns a deferred that is fired with the body of the response.

        :param url: The URL for the request.
        :type url: str
        :param method: The HTTP method of the request.
        :type method: str
        :param body: The body of the request, if any.
        :type body: str
        :param headers: The headers of the request.
        :type headers: dict
        :param callback: A callback to be added to the request's deferred
                         callback chain.
        :type callback: callable

        :return: A deferred that fires with the body of the request.
        :rtype: twisted.internet.defer.Deferred
        """
        leap_assert(
            callable(callback),
            message="The callback parameter should be a callable!")
        return self._semaphore.run(self._request, url, method, body, headers,
                                   callback)

    def close(self):
        """
        Close any cached connections.
        """
        self._pool.closeCachedConnections()

#
# An IBodyProducer to write the body of an HTTP request as a string.
#


class _StringBodyProducer(object):
    """
    A producer that writes the body of a request to a consumer.
    """

    implements(IBodyProducer)

    def __init__(self, body):
        """
        Initialize the string produer.

        :param body: The body of the request.
        :type body: str
        """
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        """
        Write the body to the consumer.

        :param consumer: Any IConsumer provider.
        :type consumer: twisted.internet.interfaces.IConsumer

        :return: A successful deferred.
        :rtype: twisted.internet.defer.Deferred
        """
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


#
# Patched twisted.web classes
#

class _HTTP11ClientProtocol(HTTP11ClientProtocol):
    """
    A timeout-able HTTP 1.1 client protocol, that is instantiated by the
    _HTTP11ClientFactory below.
    """

    def __init__(self, quiescentCallback, timeout):
        """
        Initialize the protocol.

        :param quiescentCallback:
        :type quiescentCallback: callable
        :param timeout: A timeout, in seconds, for requests made by this
                        protocol.
        :type timeout: float
        """
        HTTP11ClientProtocol.__init__(self, quiescentCallback)
        self._timeout = timeout
        self._timeoutCall = None

    def request(self, request):
        """
        Issue request over self.transport and return a Deferred which
        will fire with a Response instance or an error.

        :param request: The object defining the parameters of the request to
                        issue.
        :type request: twisted.web._newclient.Request

        :return: A deferred which fires after the request has finished.
        :rtype: Deferred
        """
        d = HTTP11ClientProtocol.request(self, request)
        if self._timeout:
            self._last_buffer_len = 0
            timeoutCall = reactor.callLater(
                self._timeout, self._doTimeout, request)
            self._timeoutCall = timeoutCall
        return d

    def _doTimeout(self, request):
        """
        Give up the request because of a timeout.

        :param request: The object defining the parameters of the request to
                        issue.
        :type request: twisted.web._newclient.Request
        """
        self._giveUp(
            failure.Failure(
                defer.TimeoutError(
                    "Getting %s took longer than %s seconds."
                    % (request.absoluteURI, self._timeout))))

    def _cancelTimeout(self):
        """
        Cancel the request timeout, when it's finished.
        """
        if self._timeoutCall and self._timeoutCall.active():
            self._timeoutCall.cancel()
            self._timeoutCall = None

    def _finishResponse(self, rest):
        """
        Cancel the timeout when finished receiving the response.
        """
        self._cancelTimeout()
        HTTP11ClientProtocol._finishResponse(self, rest)

    def dataReceived(self, bytes):
        """
        Receive some data and extend the timeout period of this request.

        :param bytes: A string of indeterminate length.
        :type bytes: str
        """
        HTTP11ClientProtocol.dataReceived(self, bytes)
        if self._timeoutCall and self._timeoutCall.active():
            self._timeoutCall.reset(self._timeout)

    def connectionLost(self, reason):
        self._cancelTimeout()
        return HTTP11ClientProtocol.connectionLost(self, reason)
