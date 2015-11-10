# -*- coding: utf-8 -*-
# test_certs.py
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
    * leap/common/certs.py
"""
import os
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from leap.common import certs
from leap.common.testing.basetest import BaseLeapTest

TEST_CERT_PEM = os.path.join(
    os.path.split(__file__)[0],
    '..', 'testing', "leaptest_combined_keycert.pem")

# Values from the test cert file:
# Not Before: Sep  3 17:52:16 2013 GMT
# Not After : Sep  1 17:52:16 2023 GMT
CERT_NOT_BEFORE = (2013, 9, 3, 17, 52, 16, 1, 246, 0)
CERT_NOT_AFTER = (2023, 9, 1, 17, 52, 16, 4, 244, 0)


class CertsTest(BaseLeapTest):

    def setUp(self):
        self.setUpEnv()

    def tearDown(self):
        self.tearDownEnv()

    def test_should_redownload_if_no_cert(self):
        self.assertTrue(certs.should_redownload(certfile=""))

    def test_should_redownload_if_invalid_pem(self):
        cert_path = self.get_tempfile('test_pem_file.pem')

        with open(cert_path, 'w') as f:
            f.write('this is some invalid data for the pem file')

        self.assertTrue(certs.should_redownload(cert_path))

    def test_should_redownload_if_before(self):
        def new_now():
            time.struct_time(CERT_NOT_BEFORE)
        self.assertTrue(certs.should_redownload(TEST_CERT_PEM, now=new_now))

    def test_should_redownload_if_after(self):
        def new_now():
            time.struct_time(CERT_NOT_AFTER)
        self.assertTrue(certs.should_redownload(TEST_CERT_PEM, now=new_now))

    def test_not_should_redownload(self):
        self.assertFalse(certs.should_redownload(TEST_CERT_PEM))

    def test_is_valid_pemfile(self):
        with open(TEST_CERT_PEM) as f:
            cert_data = f.read()

        self.assertTrue(certs.is_valid_pemfile(cert_data))

    def test_not_is_valid_pemfile(self):
        cert_data = 'this is some invalid data for the pem file'

        self.assertFalse(certs.is_valid_pemfile(cert_data))

    def test_get_cert_time_boundaries(self):
        """
        This test ensures us that the returned values are returned in UTC/GMT.
        """
        with open(TEST_CERT_PEM) as f:
            cert_data = f.read()

        valid_from, valid_to = certs.get_cert_time_boundaries(cert_data)
        self.assertEqual(tuple(valid_from), CERT_NOT_BEFORE)
        self.assertEqual(tuple(valid_to), CERT_NOT_AFTER)


if __name__ == "__main__":
    unittest.main()
