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

import requests

try:
    import simplejson as json
except ImportError:
    import json  # noqa

from leap.common.check import leap_assert
from leap.common.keymanager.errors import (
    KeyNotFound,
    NoPasswordGiven,
)
from leap.common.keymanager.keys import (
    build_key_from_dict,
)
from leap.common.keymanager.openpgp import (
    OpenPGPKey,
    OpenPGPScheme,
    encrypt_sym,
)


TAGS_INDEX = 'by-tags'
TAGS_AND_PRIVATE_INDEX = 'by-tags-and-private'
INDEXES = {
    TAGS_INDEX: ['tags'],
    TAGS_AND_PRIVATE_INDEX: ['tags', 'bool(private)'],
}


class KeyManager(object):

    def __init__(self, address, nickserver_url, soledad, token=None):
        """
        Initialize a Key Manager for user's C{address} with provider's
        nickserver reachable in C{url}.

        @param address: The address of the user of this Key Manager.
        @type address: str
        @param url: The URL of the nickserver.
        @type url: str
        @param soledad: A Soledad instance for local storage of keys.
        @type soledad: leap.soledad.Soledad
        """
        self._address = address
        self._nickserver_url = nickserver_url
        self._soledad = soledad
        self.token = token
        self._wrapper_map = {
            OpenPGPKey: OpenPGPScheme(soledad),
            # other types of key will be added to this mapper.
        }
        self._init_indexes()
        self._fetcher = requests

    #
    # utilities
    #

    def _key_class_from_type(self, ktype):
        """
        Return key class from string representation of key type.
        """
        return filter(
            lambda klass: str(klass) == ktype,
            self._wrapper_map).pop()

    def _init_indexes(self):
        """
        Initialize the database indexes.
        """
        # Ask the database for currently existing indexes.
        db_indexes = dict(self._soledad.list_indexes())
        # Loop through the indexes we expect to find.
        for name, expression in INDEXES.items():
            if name not in db_indexes:
                # The index does not yet exist.
                self._soledad.create_index(name, *expression)
                continue
            if expression == db_indexes[name]:
                # The index exists and is up to date.
                continue
            # The index exists but the definition is not what expected, so we
            # delete it and add the proper index expression.
            self._soledad.delete_index(name)
            self._soledad.create_index(name, *expression)

    def _get_dict_from_http_json(self, path):
        """
        Make a GET HTTP request and return a dictionary containing the
        response.
        """
        response = self._fetcher.get(self._nickserver_url+path)
        leap_assert(response.status_code == 200, 'Invalid response.')
        leap_assert(
            response.headers['content-type'].startswith('application/json')
                is True,
            'Content-type is not JSON.')
        return response.json()

    #
    # key management
    #

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

        @param ktype: The type of the key.
        @type ktype: KeyType

        @raise httplib.HTTPException:
        @raise KeyNotFound: If the key was not found both locally and in
            keyserver.
        """
        # prepare the public key bound to address
        pubkey = self.get_key(
            self._address, ktype, private=False, fetch_remote=False)
        data = {
            'address': self._address,
            'keys': [
                json.loads(pubkey.get_json()),
            ]
        }
        # prepare the private key bound to address
        if send_private:
            if password is None or password == '':
                raise NoPasswordGiven('Can\'t send unencrypted private keys!')
            privkey = self.get_key(
                self._address, ktype, private=True, fetch_remote=False)
            privkey = json.loads(privkey.get_json())
            privkey.key_data = encrypt_sym(privkey.key_data, password)
            data['keys'].append(privkey)
        self._fetcher.put(
            self._nickserver_url + '/key/' + self._address,
            data=data,
            auth=(self._address, self._token))

    def get_key(self, address, ktype, private=False, fetch_remote=True):
        """
        Return a key of type C{ktype} bound to C{address}.

        First, search for the key in local storage. If it is not available,
        then try to fetch from nickserver.

        @param address: The address bound to the key.
        @type address: str
        @param ktype: The type of the key.
        @type ktype: KeyType
        @param private: Look for a private key instead of a public one?
        @type private: bool

        @return: A key of type C{ktype} bound to C{address}.
        @rtype: EncryptionKey
        @raise KeyNotFound: If the key was not found both locally and in
            keyserver.
        """
        leap_assert(
            ktype in self._wrapper_map,
            'Unkown key type: %s.' % str(ktype))
        try:
            return self._wrapper_map[ktype].get_key(address, private=private)
        except KeyNotFound:
            if fetch_remote is False:
                raise
            # fetch keys from server and discard unwanted types.
            keys = filter(lambda k: isinstance(k, ktype),
                          self.fetch_keys_from_server(address))
            if len(keys) is 0:
                raise KeyNotFound()
            leap_assert(
                len(keys) == 1,
                'Got more than one key of type %s for %s.' %
                (str(ktype), address))
            self._wrapper_map[ktype].put_key(keys[0])
            return self._wrapper_map[ktype].get_key(address, private=private)

    def fetch_keys_from_server(self, address):
        """
        Fetch keys bound to C{address} from nickserver.

        @param address: The address bound to the keys.
        @type address: str

        @return: A list of keys bound to C{address}.
        @rtype: list of EncryptionKey
        @raise KeyNotFound: If the key was not found on nickserver.
        @raise httplib.HTTPException:
        """
        keydata = self._get_dict_from_http_json('/key/%s' % address)
        leap_assert(
            keydata['address'] == address,
            "Fetched key for wrong address.")
        keys = []
        for key in keydata['keys']:
            keys.append(
                build_key_from_dict(
                    self._key_class_from_type(key['type']),
                    address,
                    key))
        return keys

    def get_all_keys_in_local_db(self, private=False):
        """
        Return all keys stored in local database.

        @return: A list with all keys in local db.
        @rtype: list
        """
        return map(
            lambda doc: build_key_from_dict(
                self._key_class_from_type(doc.content['type']),
                doc.content['address'],
                doc.content),
            self._soledad.get_from_index(
                TAGS_AND_PRIVATE_INDEX,
                'keymanager-key',
                '1' if private else '0'))

    def refresh_keys(self):
        """
        Fetch keys from nickserver and update them locally.
        """
        addresses = set(map(
            lambda doc: doc.address,
            self.get_all_keys_in_local_db(private=False)))
        # TODO: maybe we should not attempt to refresh our own public key?
        for address in addresses:
            for key in self.fetch_keys_from_server(address):
                self._wrapper_map[key.__class__].put_key(key)

    def gen_key(self, ktype):
        """
        Generate a key of type C{ktype} bound to the user's address.

        @param ktype: The type of the key.
        @type ktype: KeyType

        @return: The generated key.
        @rtype: EncryptionKey
        """
        return self._wrapper_map[ktype].gen_key(self._address)

    #
    # Token setter/getter
    #

    def _get_token(self):
        return self._token

    def _set_token(self, token):
        self._token = token

    token = property(
        _get_token, _set_token, doc='The auth token.')
