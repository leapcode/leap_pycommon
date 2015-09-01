# -*- coding: utf-8 -*-
# plugins.py
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
Twisted plugins leap utilities.
"""
import os.path

from twisted.plugin import getPlugins

from leap.common.config import get_path_prefix

# A whitelist of modules from where to collect plugins dynamically.
# For the moment restricted to leap namespace, but the idea is that we can pass
# other "trusted" modules as options to the initialization of soledad.

# TODO discover all the namespace automagically

PLUGGABLE_LEAP_MODULES = ('mail', 'keymanager')

_preffix = get_path_prefix()
rc_file = os.path.join(_preffix, "leap", "leap.cfg")


def _get_extra_pluggable_modules():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read(rc_file)
    try:
        modules = eval(
            config.get('plugins', 'extra_pluggable_modules'), {}, {})
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError,
            ConfigParser.MissingSectionHeaderError):
        modules = []
    return modules

if os.path.isfile(rc_file):
    # TODO in the case of being called from the standalone client,
    # we should pass the flag in some other way.
    EXTRA_PLUGGABLE_MODULES = _get_extra_pluggable_modules()
else:
    EXTRA_PLUGGABLE_MODULES = []


def collect_plugins(interface):
    """
    Traverse a whitelist of modules and collect all the plugins that implement
    the passed interface.
    """
    plugins = []
    for namespace in PLUGGABLE_LEAP_MODULES:
        try:
            module = __import__('leap.%s.plugins' % namespace, fromlist='.')
            plugins = plugins + list(getPlugins(interface, module))
        except ImportError:
            pass
    for namespace in EXTRA_PLUGGABLE_MODULES:
        try:
            module = __import__('%s.plugins' % namespace, fromlist='.')
            plugins = plugins + list(getPlugins(interface, module))
        except ImportError:
            pass
    return plugins
