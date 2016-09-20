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
    * leap/common/check.py
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock

from leap.common import check


class CheckTests(unittest.TestCase):
    def test_raises_on_false_condition(self):
        with self.assertRaises(AssertionError):
            check.leap_assert(False, "Condition")

    def test_raises_on_none_condition(self):
        with self.assertRaises(AssertionError):
            check.leap_assert(None, "Condition")

    def test_suceeds_with_good_condition(self):
        check.leap_assert(True, "")

    def test_raises_on_bad_type(self):
        with self.assertRaises(AssertionError):
            check.leap_assert_type(42, str)

    def test_succeeds_on_good_type(self):
        check.leap_assert_type(42, int)

    @mock.patch("traceback.extract_stack", mock.MagicMock(return_value=None))
    def test_does_not_raise_on_bug(self):
        with self.assertRaises(AssertionError):
            check.leap_assert(False, "")
