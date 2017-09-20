# -*- coding: utf-8 -*-
# files.py
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
Implements file helper methods
"""

import errno
import logging
import os
import stat
import time

logger = logging.getLogger(__name__)


def check_and_fix_urw_only(cert):
    """
    Test for 600 mode and try to set it if anything different found

    Might raise OSError

    :param cert: Certificate path
    :type cert: str
    """
    mode = stat.S_IMODE(os.stat(cert).st_mode)

    if mode != int('600', 8):
        try:
            logger.warning('Bad permission on %s attempting to set 600' %
                           (cert,))
            os.chmod(cert, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.error('Error while trying to chmod 600 %s' %
                         cert)
            raise


def get_mtime(filename):
    """
    Returns the modified time or None if the file doesn't exist

    :param filename: path to check
    :type filename: str

    :rtype: str
    """
    try:
        return time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT', time.gmtime(
                os.path.getmtime(filename)))
    except OSError:
        return None


def mkdir_p(path):
    """
    Creates the path and all the intermediate directories that don't
    exist

    Might raise OSError

    :param path: path to create
    :type path: str
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# Twisted implementation of which
def which(name, flags=os.X_OK, path_extension="/usr/sbin:/sbin"):
    """
    Search PATH for executable files with the given name.

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    :type name: C{str}
    :param name: The name for which to search.

    :type flags: C{int}
    :param flags: Arguments to L{os.access}.

    :rtype: C{list}
    :param: A list of the full paths to files found, in the
    order in which they were found.
    """

    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    path = path_extension + os.pathsep + path
    if path is None:
        return []
    parts = path.split(os.pathsep)
    for p in parts:
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result
