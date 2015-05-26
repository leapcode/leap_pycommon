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

import os

from zope.interface import implements

from OpenSSL.crypto import load_certificate
from OpenSSL.crypto import FILETYPE_PEM

from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.ssl import CertificateOptions
from twisted.internet.defer import succeed

from twisted.web.client import Agent
from twisted.web.client import HTTPConnectionPool
from twisted.web.client import readBody
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer


class HTTPClient(object):
    """
    HTTP client done the twisted way, with a main focus on pinning the SSL
    certificate.
    """

    def __init__(self, cert_file=None):
        """
        Init the HTTP client

        :param cert_file: The path to the certificate file, if None given the
                          system's CAs will be used.
        :type cert_file: str
        """
        self._pool = HTTPConnectionPool(reactor, persistent=True)
        self._pool.maxPersistentPerHost = 10

        if cert_file:
            cert = self._load_cert(cert_file)
            self._agent = Agent(
                reactor,
                HTTPClient.ClientContextFactory(cert),
                pool=self._pool)
        else:
            # trust the system's CAs
            self._agent = Agent(
                reactor,
                BrowserLikePolicyForHTTPS(),
                pool=self._pool)

    def _load_cert(self, cert_file):
        """
        Load a X509 certificate from a file.

        :param cert_file: The path to the certificate file.
        :type cert_file: str

        :return: The X509 certificate.
        :rtype: OpenSSL.crypto.X509
        """
        if os.path.exists(cert_file):
            with open(cert_file) as f:
                data = f.read()
                return load_certificate(FILETYPE_PEM, data)

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
        d = self._agent.request(
            method, url, headers=Headers(headers), bodyProducer=body)
        d.addCallback(readBody)
        return d

    class ClientContextFactory(ClientContextFactory):
        """
        A context factory that will verify the server's certificate against a
        given CA certificate.
        """

        def __init__(self, cacert):
            """
            Initialize the context factory.

            :param cacert: The CA certificate.
            :type cacert: OpenSSL.crypto.X509
            """
            self._cacert = cacert

        def getContext(self, hostname, port):
            opts = CertificateOptions(verify=True, caCerts=[self._cacert])
            return opts.getContext()

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
