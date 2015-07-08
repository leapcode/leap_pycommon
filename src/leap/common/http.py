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
except ImportError:
    print "*******"
    print "Twisted is needed to use leap.common.http module"
    print ""
    print "Install the extra requirement of the package:"
    print "$ pip install leap.common[Twisted]"
    import sys
    sys.exit(1)


from leap.common.certs import get_compatible_ssl_context_factory

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet.defer import succeed

from twisted.web.client import Agent
from twisted.web.client import HTTPConnectionPool
from twisted.web.client import readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer


def createPool(maxPersistentPerHost=10, persistent=True):
    pool = HTTPConnectionPool(reactor, persistent)
    pool.maxPersistentPerHost = maxPersistentPerHost
    return pool

_pool = createPool()


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

    def __init__(self, cert_file=None, pool=_pool):
        """
        Init the HTTP client

        :param cert_file: The path to the certificate file, if None given the
                          system's CAs will be used.
        :type cert_file: str
        :param pool: An optional dedicated connection pool to override the
                     default shared one.
        :type pool: HTTPConnectionPool
        """

        policy = get_compatible_ssl_context_factory(cert_file)

        self._pool = pool
        self._agent = Agent(
            reactor,
            policy,
            pool=pool)
        self._semaphore = defer.DeferredSemaphore(pool.maxPersistentPerHost)

    def request(self, url, method='GET', body=None, headers={}):
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

        :return: A deferred that fires with the body of the request.
        :rtype: twisted.internet.defer.Deferred
        """
        if body:
            body = HTTPClient.StringBodyProducer(body)
        d = self._semaphore.run(self._agent.request,
                                method, url, headers=Headers(headers),
                                bodyProducer=body)
        d.addCallback(readBody)
        return d

    def close(self):
        """
        Close any cached connections.
        """
        self._pool.closeCachedConnections()

    class StringBodyProducer(object):
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
            return succeed(None)

        def pauseProducing(self):
            pass

        def stopProducing(self):
            pass
