# -*- coding: utf-8 -*-
# baseconfig.py
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
Implements the abstract base class for configuration
"""

import copy
import logging
import functools
import os

from abc import ABCMeta, abstractmethod

from leap.common.check import leap_assert, leap_check
from leap.common.files import mkdir_p
from leap.common.config.pluggableconfig import PluggableConfig
from leap.common.config import get_path_prefix

logger = logging.getLogger(__name__)


class NonExistingSchema(Exception):
    """
    Raised if the schema needed to verify the config is None.
    """


class BaseConfig:
    """
    Abstract base class for any JSON based configuration.
    """

    __metaclass__ = ABCMeta

    """
    Standalone is a class wide parameter.

    :param standalone: if True it will return the prefix for a
                       standalone application. Otherwise, it will
                       return the system
                       default for configuration storage.
    :type standalone: bool
    """
    standalone = False

    def __init__(self):
        self._data = {}
        self._config_checker = None
        self._api_version = None

    @abstractmethod
    def _get_schema(self):
        """
        Returns the schema corresponding to the version given.

        :rtype: dict or None if the version is not supported.
        """
        pass

    def _get_spec(self):
        """
        Returns the spec object for the specific configuration.

        :rtype: dict or None if the version is not supported.
        """
        leap_assert(self._api_version is not None,
                    "You should set the API version.")

        return self._get_schema()

    def _safe_get_value(self, key):
        """
        Tries to return a value only if the config has already been loaded.

        :rtype: depends on the config structure, dict, str, array, int
        :return: returns the value for the specified key in the config
        """
        leap_assert(self._config_checker, "Load the config first")
        return self._config_checker.config.get(key, None)

    def set_api_version(self, version):
        """
        Sets the supported api version.

        :param api_version: the version of the api supported by the provider.
        :type api_version: str
        """
        self._api_version = version
        leap_assert(self._get_schema() is not None,
                    "Version %s is not supported." % (version, ))

    def get_path_prefix(self):
        """
        Returns the platform dependant path prefixer
        """
        return get_path_prefix(standalone=self.standalone)

    def loaded(self):
        """
        Returns True if the configuration has been already
        loaded. False otherwise
        """
        return self._config_checker is not None

    def save(self, path_list):
        """
        Saves the current configuration to disk.

        :param path_list: list of components that form the relative
                          path to configuration. The absolute path
                          will be calculated depending on the platform.
        :type path_list: list

        :return: True if saved to disk correctly, False otherwise
        """
        config_path = os.path.join(self.get_path_prefix(), *(path_list[:-1]))
        mkdir_p(config_path)

        try:
            self._config_checker.serialize(os.path.join(config_path,
                                                        path_list[-1]))
        except Exception as e:
            logger.warning("%s" % (e,))
            raise
        return True

    def load(self, path="", data=None, mtime=None, relative=True):
        """
        Loads the configuration from disk.
        It may raise NonExistingSchema exception.

        :param path: if relative=True, this is a relative path
                     to configuration. The absolute path
                     will be calculated depending on the platform
        :type path: str

        :param relative: if True, path is relative. If False, it's absolute.
        :type relative: bool

        :return: True if loaded from disk correctly, False otherwise
        :rtype: bool
        """

        if relative is True:
            config_path = os.path.join(
                self.get_path_prefix(), path)
        else:
            config_path = path

        schema = self._get_spec()
        leap_check(schema is not None,
                   "There is no schema to use.", NonExistingSchema)

        self._config_checker = PluggableConfig(format="json")
        self._config_checker.options = copy.deepcopy(schema)

        try:
            if data is None:
                self._config_checker.load(fromfile=config_path, mtime=mtime)
            else:
                self._config_checker.load(data, mtime=mtime)
        except Exception as e:
            logger.error("Something went wrong while loading " +
                         "the config from %s\n%s" % (config_path, e))
            self._config_checker = None
            return False
        return True


class LocalizedKey(object):
    """
    Decorator used for keys that are localized in a configuration.
    """

    def __init__(self, func, **kwargs):
        self._func = func

    def __call__(self, instance, lang=None):
        """
        Tries to return the string for the specified language, otherwise
        returns the default language string.

        :param lang: language code
        :type lang: str

        :return: localized value from the possible values returned by
                 self._func
                 It returns None in case that the provider does not provides
                 a matching pair of default_language and string for
                 that language.
                 e.g.:
                     'default_language': 'es',
                     'description': {'en': 'test description'}
                Note that the json schema can't check that.
        """
        descriptions = self._func(instance)
        config_lang = instance.get_default_language()
        if lang is None:
            lang = config_lang

        for key in descriptions.keys():
            if lang.startswith(key):
                config_lang = key
                break

        description_lang = descriptions.get(config_lang)
        if description_lang is None:
            logger.error("There is a misconfiguration in the "
                         "provider's language strings.")

        return description_lang

    def __get__(self, instance, instancetype):
        """
        Implement the descriptor protocol to make decorating instance
        method possible.
        """
        # Return a partial function with the first argument is the instance
        # of the class decorated.
        return functools.partial(self.__call__, instance)

if __name__ == "__main__":
    try:
        config = BaseConfig()  # should throw TypeError for _get_spec
    except Exception as e:
        assert isinstance(e, TypeError), "Something went wrong"
        print "Abstract BaseConfig class is working as expected"
