# -*- coding: utf-8 -*-
# ca_bundle.py
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
This module returns the preferred default CA certificate bundle.

If you are packaging Requests, e.g., for a Linux distribution or a managed
environment, you can change the definition of where() to return a separately
packaged CA bundle.
"""
import os.path
import platform
import sys

_system = platform.system()

IS_MAC = _system == "Darwin"


def where():
    """
    Return the preferred certificate bundle.
    :rtype: str
    """
    if getattr(sys, 'frozen', False):
        # we are running in a |PyInstaller| bundle
        path = sys._MEIPASS
        return os.path.join(path, 'cacert.pem')
    return os.path.join(os.path.dirname(__file__), 'cacert.pem')

if __name__ == '__main__':
    print(where())
