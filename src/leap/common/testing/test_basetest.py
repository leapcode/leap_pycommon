# -*- coding: utf-8 -*-
# test_basetest.py
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
Unittests for BaseLeapTest ...becase it's oh so meta
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import StringIO

from leap.common.testing.basetest import BaseLeapTest

_tempdir = None  # global for tempdir checking


class _TestCaseRunner(object):
    """
    TestCaseRunner used to run BaseLeapTest
    """
    def run_testcase(self, testcase=None):
        """
        Runs a given TestCase

        :param testcase: the testcase
        :type testcase: unittest.TestCase
        """
        if not testcase:
            return None
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(testcase)

        # Create runner, and run testcase
        io = StringIO.StringIO()
        runner = unittest.TextTestRunner(stream=io)
        results = runner.run(suite)
        return results


class TestAbstractBaseLeapTest(unittest.TestCase, _TestCaseRunner):
    """
    TestCase for BaseLeapTest abs
    """
    def test_abstract_base_class(self):
        """
        Test errors raised when setup/teardown not overloaded
        """
        class _BaseTest(BaseLeapTest):
            def test_dummy_method(self):
                pass

            def test_tautology(self):
                assert True

        results = self.run_testcase(_BaseTest)

        # should be 2 errors: NotImplemented
        # raised for setUp/tearDown
        self.assertEquals(results.testsRun, 2)
        self.assertEquals(len(results.failures), 0)
        self.assertEquals(len(results.errors), 2)


class TestInitBaseLeapTest(BaseLeapTest):
    """
    TestCase for testing initialization of BaseLeapTest
    """

    def setUp(self):
        self.setUpEnv()

    def tearDown(self):
        self.tearDownEnv()

    def test_path_is_changed(self):
        """tests whether we have changed the PATH env var"""
        os_path = os.environ['PATH']
        self.assertTrue(os_path.startswith(self.tempdir))

    def test_old_path_is_saved(self):
        """tests whether we restore the PATH env var"""
        self.assertTrue(len(self.old_path) > 1)


class TestCleanedBaseLeapTest(unittest.TestCase, _TestCaseRunner):
    """
    TestCase for testing tempdir creation and cleanup
    """

    def test_tempdir_is_cleaned_after_tests(self):
        """
        test if a TestCase derived from BaseLeapTest creates and cleans the
        temporal dir
        """
        class _BaseTest(BaseLeapTest):
            def setUp(self):
                """set global _tempdir to this instance tempdir"""
                global _tempdir
                _tempdir = self.tempdir

            def tearDown(self):
                """nothing"""
                pass

            def test_tempdir_created(self):
                """test if tempdir was created"""
                self.assertTrue(os.path.isdir(self.tempdir))

            def test_tempdir_created_on_setupclass(self):
                """test if tempdir is the one created by setupclass"""
                self.assertEqual(_tempdir, self.tempdir)

        results = self.run_testcase(_BaseTest)
        self.assertEquals(results.testsRun, 2)
        self.assertEquals(len(results.failures), 0)
        self.assertEquals(len(results.errors), 0)

        # did we cleaned the tempdir?
        self.assertFalse(os.path.isdir(_tempdir))

if __name__ == "__main__":
    unittest.main()
