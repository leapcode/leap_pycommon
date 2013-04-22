# -*- coding: utf-8 -*-
# http.py
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
HTTP utilities.
"""


import urlparse
import httplib


def HTTPClient(object):
    """
    A simple HTTP client for making requests.
    """

    def __init__(self, url):
        """
        Initialize the HTTP client.
        """
        self._url = urlparse.urlsplit(url)
        self._conn = None

    def _ensure_connection(self):
        """
        Ensure the creation of the connection object.
        """
        if self._conn is not None:
            return
        if self._url.scheme == 'https':
            connClass = httplib.HTTPSConnection
        else:
            connClass = httplib.HTTPConnection
        self._conn = connClass(self._url.hostname, self._url.port)

    def request(method, url_query, body, headers):
        """
        Make an HTTP request.

        @param method: The method of the request.
        @type method: str
        @param url_query: The URL query string of the request.
        @type url_query: str
        @param body: The body of the request.
        @type body: str
        @param headers: Headers to be sent on the request.
        @type headers: list of str
        """
        self._ensure_connection()
        return self._conn.request(mthod, url_query, body, headers)

    def response(self):
        """
        Return the response of an HTTP request.
        """
        return self._conn.getresponse()

    def read_response(self):
        """
        Get the contents of a response for an HTTP request.
        """
        return self.response().read()
