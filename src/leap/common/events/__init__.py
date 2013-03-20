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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from leap.common.events import (
    signal_pb2,
)


# the `registered_callbacks` dictionary below should have the following
# format:
#
#     { component: [ (uid, callback), ... ], ... }
#
registered_callbacks = {}


def register(signal, callback, uid=None, replace=False):
    """
    Registers `callback` to be called when `signal` is signaled.
    """
    if not registered_callbacks.has_key(signal):
        registered_callbacks[signal] = []
    cbklist = registered_callbacks[signal]
    if uid and filter(lambda (x,y): x == uid, cbklist):
        # TODO: create appropriate exception
        if not replace:
            raise Exception("Callback already registered.")
        else:
            registered_callbacks[signal] = filter(lambda(x,y): x != uid,
                                                  cbklist)
    registered_callbacks[signal].append((uid, callback))
    return uid

#def get_registered_callbacks():
#    return registered_callbacks

#__all__ = ['signal_pb2', 'service', 'register', 'registered_callbacks']
