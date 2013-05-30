# -*- coding: utf-8 -*-
# keys.py
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
Abstact key type and encryption scheme representations.
"""


try:
    import simplejson as json
except ImportError:
    import json  # noqa
import re


from hashlib import sha256
from abc import ABCMeta, abstractmethod
from leap.common.check import leap_assert


#
# Key handling utilities
#

def is_address(address):
    """
    Return whether the given C{address} is in the form user@provider.

    @param address: The address to be tested.
    @type address: str
    @return: Whether C{address} is in the form user@provider.
    @rtype: bool
    """
    return bool(re.match('[\w.-]+@[\w.-]+', address))


def build_key_from_dict(kClass, address, kdict):
    """
    Build an C{kClass} key bound to C{address} based on info in C{kdict}.

    @param address: The address bound to the key.
    @type address: str
    @param kdict: Dictionary with key data.
    @type kdict: dict
    @return: An instance of the key.
    @rtype: C{kClass}
    """
    leap_assert(address == kdict['address'], 'Wrong address in key data.')
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


def keymanager_doc_id(ktype, address, private=False):
    """
    Return the document id for the document containing a key for
    C{address}.

    @param address: The type of the key.
    @type address: KeyType
    @param address: The address bound to the key.
    @type address: str
    @param private: Whether the key is private or not.
    @type private: bool
    @return: The document id for the document that stores a key bound to
        C{address}.
    @rtype: str
    """
    leap_assert(is_address(address), "Wrong address format: %s" % address)
    ktype = str(ktype)
    visibility = 'private' if private else 'public'
    return sha256('keymanager-'+address+'-'+ktype+'-'+visibility).hexdigest()


#
# Abstraction for encryption keys
#

class EncryptionKey(object):
    """
    Abstract class for encryption keys.

    A key is "validated" if the nicknym agent has bound the user address to a
    public key. Nicknym supports three different levels of key validation:

    * Level 3 - path trusted: A path of cryptographic signatures can be traced
      from a trusted key to the key under evaluation. By default, only the
      provider key from the user's provider is a "trusted key".
    * level 2 - provider signed: The key has been signed by a provider key for
      the same domain, but the provider key is not validated using a trust
      path (i.e. it is only registered)
    * level 1 - registered: The key has been encountered and saved, it has no
      signatures (that are meaningful to the nicknym agent).
    """

    __metaclass__ = ABCMeta

    def __init__(self, address, key_id=None, fingerprint=None,
                 key_data=None, private=None, length=None, expiry_date=None,
                 validation=None, first_seen_at=None, last_audited_at=None):
        self.address = address
        self.key_id = key_id
        self.fingerprint = fingerprint
        self.key_data = key_data
        self.private = private
        self.length = length
        self.expiry_date = expiry_date
        self.validation = validation
        self.first_seen_at = first_seen_at
        self.last_audited_at = last_audited_at

    def get_json(self):
        """
        Return a JSON string describing this key.

        @return: The JSON string describing this key.
        @rtype: str
        """
        return json.dumps({
            'address': self.address,
            'type': str(self.__class__),
            'key_id': self.key_id,
            'fingerprint': self.fingerprint,
            'key_data': self.key_data,
            'private': self.private,
            'length': self.length,
            'expiry_date': self.expiry_date,
            'validation': self.validation,
            'first_seen_at': self.first_seen_at,
            'last_audited_at': self.last_audited_at,
            'tags': ['keymanager-key'],
        })


#
# Encryption schemes
#

class EncryptionScheme(object):
    """
    Abstract class for Encryption Schemes.

    A wrapper for a certain encryption schemes should know how to get and put
    keys in local storage using Soledad, how to generate new keys and how to
    find out about possibly encrypted content.
    """

    __metaclass__ = ABCMeta

    def __init__(self, soledad):
        """
        Initialize this Encryption Scheme.

        @param soledad: A Soledad instance for local storage of keys.
        @type soledad: leap.soledad.Soledad
        """
        self._soledad = soledad

    @abstractmethod
    def get_key(self, address, private=False):
        """
        Get key from local storage.

        @param address: The address bound to the key.
        @type address: str
        @param private: Look for a private key instead of a public one?
        @type private: bool

        @return: The key bound to C{address}.
        @rtype: EncryptionKey
        @raise KeyNotFound: If the key was not found on local storage.
        """
        pass

    @abstractmethod
    def put_key(self, key):
        """
        Put a key in local storage.

        @param key: The key to be stored.
        @type key: EncryptionKey
        """
        pass

    @abstractmethod
    def gen_key(self, address):
        """
        Generate a new key.

        @param address: The address bound to the key.
        @type address: str

        @return: The key bound to C{address}.
        @rtype: EncryptionKey
        """
        pass

    @abstractmethod
    def delete_key(self, key):
        """
        Remove C{key} from storage.

        @param key: The key to be removed.
        @type key: EncryptionKey
        """
        pass
