# -*- coding: utf-8 -*-
# decorators.py
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
Useful decorators.
"""
import collections
import functools
import logging

logger = logging.getLogger(__name__)


class _memoized(object):
    """
    Decorator.

    Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """
    def __init__(self, func, ignore_kwargs=None, is_method=False):
        """
        :param ignore_kwargs: If True, ignore all kwargs.
                              If tuple, ignore those kwargs.
        :type ignore_kwargs: bool, tuple or None
        :param is_method: whether the decorated function is a method.
                          (ignores the self argument if so).
        :type is_method: True
        """
        self.ignore_kwargs = ignore_kwargs if ignore_kwargs else []
        self.is_method = is_method
        self.func = func

        # TODO should put bounds to the cache dict so we do not
        # consume a huge amount of memory.
        self.cache = {}

    def __call__(self, *args, **kwargs):
        """
        Executes the call.

        :tyoe args: tuple
        :type kwargs: dict
        """
        if self.is_method:
            # forget about `self` as key
            key_args = args[1:]
        if self.ignore_kwargs is True:
            key = key_args
        else:
            key = (key_args, frozenset(
                [(k, v) for k, v in kwargs.items()
                 if k not in self.ignore_kwargs]))

        if not isinstance(key, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            logger.warning("Key is not hashable, bailing out!")
            return self.func(*args, **kwargs)

        if key in self.cache:
            logger.debug("Got value from cache...")
            return self.cache[key]
        else:
            try:
                value = self.func(*args, **kwargs)
            except Exception as exc:
                logger.error("Exception while calling function: %r" % (exc,))
                value = None
            self.cache[key] = value
            return value

    def __repr__(self):
        """
        Return the function's docstring.
        """
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """
        Support instance methods.
        """
        return functools.partial(self.__call__, obj)


def memoized_method(function=None, ignore_kwargs=None):
    """
    Wrap _memoized to allow for deferred calling

    :type function: callable, or None.
    :type ignore_kwargs: None, True or tuple.
    """
    if function:
        return _memoized(function, is_method=True)
    else:
        def wrapper(function):
            return _memoized(
                function, ignore_kwargs=ignore_kwargs, is_method=True)
        return wrapper
