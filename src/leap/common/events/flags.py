# -*- coding: utf-8 -*-
# __init__.py
# Copyright (C) 2015 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Flags for the events framework.
"""
from leap.common.check import leap_assert

EVENTS_ENABLED = True


def set_events_enabled(flag):
    leap_assert(isinstance(flag, bool))
    global EVENTS_ENABLED
    EVENTS_ENABLED = flag
