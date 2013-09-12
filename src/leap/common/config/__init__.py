# -*- coding: utf-8 -*-
# __init__.py
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
Common configs
"""
import os

from dirspec.basedir import get_xdg_config_home


def get_path_prefix(standalone=False):
    """
    Returns the platform dependent path prefix.

    :param standalone: if True it will return the prefix for a standalone
                       application.
                       Otherwise, it will return the system default for
                       configuration storage.
    :type standalone: bool
    """
    config_home = get_xdg_config_home()
    if standalone:
        config_home = os.path.join(os.getcwd(), "config")

    return config_home
