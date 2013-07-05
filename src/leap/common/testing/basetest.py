# -*- coding: utf-8 -*-
# basetest.py
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
Common testing facilities
"""
import os
import platform
import shutil
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from leap.common.check import leap_assert
from leap.common.files import mkdir_p, check_and_fix_urw_only


class BaseLeapTest(unittest.TestCase):
    """
    Base Leap TestCase
    """
    __name__ = "leap_test"
    _system = platform.system()

    @classmethod
    def setUpClass(cls):
        """
        Sets up common facilities for testing this TestCase:
        - custom PATH and HOME environmental variables
        - creates a temporal folder to which those point.
        It saves the old path and home vars so they can be restored later.
        """
        cls.old_path = os.environ['PATH']
        cls.old_home = os.environ['HOME']
        cls.tempdir = tempfile.mkdtemp(prefix="leap_tests-")
        cls.home = cls.tempdir
        bin_tdir = os.path.join(
            cls.tempdir,
            'bin')
        os.environ["PATH"] = bin_tdir
        os.environ["HOME"] = cls.tempdir

    @classmethod
    def tearDownClass(cls):
        """
        Cleanup common facilities used for testing this TestCase:
        - restores the default PATH and HOME variables
        - removes the temporal folder
        """
        os.environ["PATH"] = cls.old_path
        os.environ["HOME"] = cls.old_home
        # safety check! please do not wipe my home...
        # XXX needs to adapt to non-linuces
        leap_assert(
            cls.tempdir.startswith('/tmp/leap_tests-') or
            cls.tempdir.startswith('/var/folder'),
            "beware! tried to remove a dir which does not "
            "live in temporal folder!")
        shutil.rmtree(cls.tempdir)

    # you have to override these methods
    # this way we ensure we did not put anything
    # here that you can forget to call.

    def setUp(self):
        """not implemented"""
        raise NotImplementedError("abstract base class")

    def tearDown(self):
        """not implemented"""
        raise NotImplementedError("abstract base class")

    #
    # helper methods
    #

    def _missing_test_for_plat(self, do_raise=False):
        """
        Raises NotImplementedError for this platform
        if do_raise is True

        :param do_raise: flag to actually raise exception
        :type do_raise: bool
        """
        if do_raise:
            raise NotImplementedError(
                "This test is not implemented "
                "for the running platform: %s" %
                self._system)

    def get_tempfile(self, filename):
        """
        Returns the path of a given filename
        prepending the temporal dir associated with this
        TestCase

        :param filename: the filename
        :type filename: str
        """
        return os.path.join(self.tempdir, filename)

    def touch(self, filepath):
        """
        Touches a filepath, creating folders along
        the way if needed.

        :param filepath: path to be touched
        :type filepath: str
        """
        folder, filename = os.path.split(filepath)
        if not os.path.isdir(folder):
            mkdir_p(folder)
        self.assertTrue(os.path.isdir(folder))
        with open(filepath, 'w') as fp:
            fp.write(' ')
        self.assertTrue(os.path.isfile(filepath))

    def chmod600(self, filepath):
        """
        Chmods 600 a file

        :param filepath: filepath to be chmodded
        :type filepath: str
        """
        check_and_fix_urw_only(filepath)
