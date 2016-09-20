# -*- coding: utf-8 -*-
# test_zmq_components.py
# Copyright (C) 2014 LEAP
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
Tests for the zmq_components module.
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from leap.common.events import zmq_components


class AddrParseTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_addr_parsing(self):
        addr_re = zmq_components.ADDRESS_RE

        self.assertEqual(
            addr_re.search("ipc:///tmp/foo/bar/baaz-2/foo.0").groups(),
            ("ipc", "/tmp/foo/bar/baaz-2/foo.0", None))
        self.assertEqual(
            addr_re.search("tcp://localhost:9000").groups(),
            ("tcp", "localhost", "9000"))
        self.assertEqual(
            addr_re.search("tcp://127.0.0.1:9000").groups(),
            ("tcp", "127.0.0.1", "9000"))


if __name__ == "__main__":
    unittest.main()
