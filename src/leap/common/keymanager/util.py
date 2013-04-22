# -*- coding: utf-8 -*-
# util.py
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


"""
Utilities for the Key Manager.
"""


import re


from hashlib import sha256
from leap.common.check import leap_assert


def _is_address(address):
    """
    Return whether the given C{address} is in the form user@provider.

    @param address: The address to be tested.
    @type address: str
    @return: Whether C{address} is in the form user@provider.
    @rtype: bool
    """
    return bool(re.match('[\w.-]+@[\w.-]+', address))


def _build_key_from_dict(kClass, address, kdict):
    """
    Build an C{kClass} key bound to C{address} based on info in C{kdict}.

    @param address: The address bound to the key.
    @type address: str
    @param kdict: Dictionary with key data.
    @type kdict: dict
    @return: An instance of the key.
    @rtype: C{kClass}
    """
    return kClass(
        address,
        key_id=kdict['key_id'],
        fingerprint=kdict['fingerprint'],
        key_data=kdict['key_data'],
        private=kdict['private'],
        length=kdict['length'],
        expiry_date=kdict['expiry_date'],
        first_seen_at=kdict['first_seen_at'],
        last_audited_at=kdict['last_audited_at'],
        validation=kdict['validation'],  # TODO: verify for validation.
    )


def _build_key_from_doc(kClass, address, doc):
    """
    Build an C{kClass} for C{address} based on C{doc} from local storage.

    @param address: The address bound to the key.
    @type address: str
    @param doc: Document obtained from Soledad storage.
    @type doc: leap.soledad.backends.leap_backend.LeapDocument
    @return: An instance of the key.
    @rtype: C{kClass}
    """
    return _build_key_from_dict(kClass, address, doc.content)


def _keymanager_doc_id(address, private=False):
    """
    Return the document id for the document containing a key for
    C{address}.

    @param address: The address bound to the key.
    @type address: str
    @param private: Whether the key is private or not.
    @type private: bool
    @return: The document id for the document that stores a key bound to
        C{address}.
    @rtype: str
    """
    leap_assert(_is_address(address), "Wrong address format: %s" % address)
    ktype = 'private' if private else 'public'
    return sha256('key-manager-'+address+'-'+ktype).hexdigest()
