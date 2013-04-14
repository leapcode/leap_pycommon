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


"""
Key Manager is a Nicknym agent for LEAP client.
"""


try:
    import simplejson as json
except ImportError:
    import json  # noqa


from abc import ABCMeta, abstractmethod
from u1db.errors import HTTPError


#
# Key types
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

    @abstractmethod
    def get_json(self):
        """
        Return a JSON string describing this key.

        @return: The JSON string describing this key.
        @rtype: str
        """


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


#
# Key manager
#


class KeyNotFound(Exception):
    """
    Raised when key was no found on keyserver.
    """


class KeyManager(object):

    def __init__(self, address, url):
        """
        Initialize a Key Manager for user's C{address} with provider's
        nickserver reachable in C{url}.

        @param address: The address of the user of this Key Manager.
        @type address: str
        @param url: The URL of the key manager.
        @type url: str
        """
        self.address = address
        self.url = url

    def send_key(self, ktype, send_private=False, password=None):
        """
        Send user's key of type C{ktype} to provider.

        Public key bound to user's is sent to provider, which will sign it and
        replace any prior keys for the same address in its database.

        If C{send_private} is True, then the private key is encrypted with
        C{password} and sent to server in the same request, together with a
        hash string of user's address and password. The encrypted private key
        will be saved in the server in a way it is publicly retrievable
        through the hash string.

        @param address: The address bound to the key.
        @type address: str
        @param ktype: The type of the key.
        @type ktype: KeyType

        @raise httplib.HTTPException:
        """

    def get_key(self, address, ktype):
        """
        Return a key of type C{ktype} bound to C{address}.

        First, search for the key in local storage. If it is not available,
        then try to fetch from nickserver.

        @param address: The address bound to the key.
        @type address: str
        @param ktype: The type of the key.
        @type ktype: KeyType

        @return: A key of type C{ktype} bound to C{address}.
        @rtype: EncryptionKey
        @raise KeyNotFound: If the key was not found both locally and in
            keyserver.
        """
        try:
            return wrapper_map[ktype].get_key(address)
        except KeyNotFound:
            key = filter(lambda k: isinstance(k, ktype),
                         self._fetch_keys(address))
            if key is None
                raise KeyNotFound()
            wrapper_map[ktype].put_key(key)
            return key


    def _fetch_keys(self, address):
        """
        Fetch keys bound to C{address} from nickserver.

        @param address: The address bound to the keys.
        @type address: str

        @return: A list of keys bound to C{address}.
        @rtype: list of EncryptionKey
        @raise KeyNotFound: If the key was not found on nickserver.
        @raise httplib.HTTPException:
        """

    def refresh_keys(self):
        """
        Update the user's db of validated keys to see if there are changes.
        """

    def gen_key(self, ktype):
        """
        Generate a key of type C{ktype} bound to the user's address.

        @param ktype: The type of the key.
        @type ktype: KeyType

        @return: The generated key.
        @rtype: EncryptionKey
        """
        return wrapper_map[ktype].gen_key(self.address)
