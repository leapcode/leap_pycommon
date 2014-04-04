# -*- coding: utf-8 -*-
# mail.py
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
Utility functions for email.
"""
import email
import re


def get_email_charset(content, default="utf-8"):
    """
    Mini parser to retrieve the charset of an email.

    :param content: mail contents
    :type content: unicode or str
    :param default: optional default value for encoding
    :type default: str or None

    :returns: the charset as parsed from the contents
    :rtype: str
    """
    if isinstance(content, unicode):
        content.encode("utf-8", "replace")

    charset = default
    try:
        em = email.message_from_string(content)
        # Miniparser for: Content-Type: <something>; charset=<charset>
        charset_re = r'''charset=(?P<charset>[\w|\d|-]*)'''
        charset = re.findall(charset_re, em["Content-Type"])[0]
        if charset is None or len(charset) == 0:
            charset = default
    except Exception:
        pass
    return charset
