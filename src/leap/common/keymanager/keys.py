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
Abstact key type and wrapper representations.
"""


from abc import ABCMeta, abstractmethod


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
                 key_data=None, length=None, expiry_date=None,
                 validation=None, first_seen_at=None,
                 last_audited_at=None):
        self.address = address
        self.key_id = key_id
        self.fingerprint = fingerprint
        self.key_data = key_data
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
            'type': str(self.__type__),
            'key_id': self.key_id,
            'fingerprint': self.fingerprint,
            'key_data': self.key_data,
            'length': self.length,
            'expiry_date': self.expiry_date,
            'validation': self.validation,
            'first_seen_at': self.first_seen_at,
            'last_audited_at': self.last_audited_at,
        })


#
# Key wrappers
#

class KeyTypeWrapper(object):
    """
    Abstract class for Key Type Wrappers.

    A wrapper for a certain key type should know how to get and put keys in
    local storage using Soledad and also how to generate new keys.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_key(self, address):
        """
        Get key from local storage.

        @param address: The address bound to the key.
        @type address: str

        @return: The key bound to C{address}.
        @rtype: EncryptionKey
        @raise KeyNotFound: If the key was not found on local storage.
        """

    @abstractmethod
    def put_key(self, key):
        """
        Put a key in local storage.

        @param key: The key to be stored.
        @type key: EncryptionKey
        """

    @abstractmethod
    def gen_key(self, address):
        """
        Generate a new key.

        @param address: The address bound to the key.
        @type address: str
        @return: The key bound to C{address}.
        @rtype: EncryptionKey
        """

