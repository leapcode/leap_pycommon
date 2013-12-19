# -*- coding: utf-8 -*-
# test_check.py
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
    * leap/common/decorators._memoized
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from time import sleep

import mock

from leap.common.decorators import _memoized


class MemoizeTests(unittest.TestCase):

    def test_memoized_call(self):
        """
        Test that a memoized function only calls once.
        """
        witness = mock.Mock()

        @_memoized
        def callmebaby():
            return witness()

        for i in range(10):
            callmebaby()
        witness.assert_called_once_with()

    def test_cache_invalidation(self):
        """
        Test that time makes the cache invalidation expire.
        """
        witness = mock.Mock()

        cache_with_alzheimer = _memoized
        cache_with_alzheimer.CACHE_INVALIDATION_DELTA = 1

        @cache_with_alzheimer
        def callmebaby(*args):
            return witness(*args)

        for i in range(10):
            callmebaby()
        witness.assert_called_once_with()

        sleep(2)
        callmebaby("onemoretime")

        expected = [mock.call(), mock.call("onemoretime")]
        self.assertEqual(
            witness.call_args_list,
            expected)


if __name__ == "__main__":
    unittest.main()
