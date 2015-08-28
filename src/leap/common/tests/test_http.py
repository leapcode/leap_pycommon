# -*- coding: utf-8 -*-
# test_http.py
# Copyright (C) 2013 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Tests for:
    * leap/common/http.py
"""
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from leap.common import http
from leap.common.testing.basetest import BaseLeapTest

TEST_CERT_PEM = os.path.join(
    os.path.split(__file__)[0],
    '..', 'testing', "leaptest_combined_keycert.pem")


class HTTPClientTest(BaseLeapTest):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_agents_sharing_pool_by_default(self):
        client = http.HTTPClient()
        client2 = http.HTTPClient(TEST_CERT_PEM)
        self.assertNotEquals(
            client._agent, client2._agent, "Expected dedicated agents")
        self.assertEquals(
            client._agent._pool, client2._agent._pool,
            "Pool was not reused by default")

    def test_agent_can_have_dedicated_custom_pool(self):
        custom_pool = http._HTTPConnectionPool(
            None,
            timeout=10,
            maxPersistentPerHost=42,
            persistent=False
        )
        self.assertEquals(custom_pool.maxPersistentPerHost, 42,
                          "Custom persistent connections "
                          "limit is not being respected")
        self.assertFalse(custom_pool.persistent,
                         "Custom persistence is not being respected")
        default_client = http.HTTPClient()
        custom_client = http.HTTPClient(pool=custom_pool)

        self.assertNotEquals(
            default_client._agent, custom_client._agent,
            "No agent reuse is expected")
        self.assertEquals(
            custom_pool, custom_client._agent._pool,
            "Custom pool usage was not respected")

if __name__ == "__main__":
    unittest.main()
