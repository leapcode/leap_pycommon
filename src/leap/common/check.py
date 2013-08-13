# -*- coding: utf-8 -*-
# check.py
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
Set of functions to help checking situations
"""

import logging
import traceback


logger = logging.getLogger(__name__)


def leap_assert(condition, message=""):
    """
    Asserts the condition and displays the message if that's not
    met. It also logs the error and its backtrace.

    :param condition: condition to check
    :type condition: bool
    :param message: message to display if the condition isn't met
    :type message: str
    """
    if not condition:
        logger.error("Bug: %s" % (message,))
        try:
            for formatted_line in traceback.format_list(
                    traceback.extract_stack()[:-1]):
                for line in formatted_line.split("\n"):
                    if len(line.strip()) > 0:
                        logger.error(line)
        except Exception as e:
            logger.error("Bug in leap_assert: %r" % (e,))
    assert condition, message


def leap_assert_type(var, expectedType):
    """
    Helper assert check for a variable's expected type

    :param var: variable to check
    :type var: any
    :param expectedType: type to check agains
    :type expectedType: type
    """
    leap_assert(isinstance(var, expectedType),
                "Expected type %r instead of %r" %
                (expectedType, type(var)))


def leap_check(condition, message="", exception=Exception):
    """
    Asserts the condition and displays the message if that's not
    met. It also logs the error and its backtrace.

    :param condition: condition to check
    :type condition: bool
    :param message: message to display if the condition isn't met
    :type message: str
    :param exception: the exception to raise in case of condition being false.
    :type exception: Exception
    """
    if not condition:
        logger.error(message)
        raise exception(message)
