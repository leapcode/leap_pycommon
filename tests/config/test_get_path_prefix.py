# -*- coding: utf-8 -*-
# test_get_path_prefix.py
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
Tests for get_path_prefix
"""
import os
import mock

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from leap.common.config import get_path_prefix
from leap.common.testing.basetest import BaseLeapTest


class GetPathPrefixTest(BaseLeapTest):
    """
    Tests for the get_path_prefix helper.

    Note: we only are testing that the path is correctly returned and that if
    we are not in a bundle (standalone=False) then the paths are different.

    xdg calculates the correct path using different methods and dlls
    (in case of Windows) so we don't implement tests to check if the paths
    are the correct ones.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_standalone_path(self):
        expected_path = os.path.join('expected', 'path', 'config')
        fake_cwd = os.path.join('expected', 'path')
        with mock.patch('os.getcwd', lambda: fake_cwd):
            path = get_path_prefix(standalone=True)
        self.assertEquals(path, expected_path)

    def test_path_prefix(self):
        standalone_path = get_path_prefix(standalone=True)
        path = get_path_prefix(standalone=False)
        self.assertNotEquals(path, standalone_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
