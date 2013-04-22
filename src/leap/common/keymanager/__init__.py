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

import httplib


from u1db.errors import HTTPError


from leap.common.check import leap_assert
from leap.common.keymanager.errors import (
    KeyNotFound,
    KeyAlreadyExists,
)
from leap.common.keymanager.openpgp import (
    OpenPGPKey,
    OpenPGPWrapper,
    _encrypt_symmetric,
)
from leap.common.keymanager.http import HTTPClient


class KeyManager(object):

    def __init__(self, address, url, soledad):
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
        self._http_client = HTTPClient(url)
        self._wrapper_map = {
            OpenPGPKey: OpenPGPWrapper(soledad),
            # other types of key will be added to this mapper.
        }

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
        @raise KeyNotFound: If the key was not found both locally and in
            keyserver.
        """
        # prepare the public key bound to address
        data = {
            'address': self._address,
            'keys': [
                json.loads(
                    self.get_key(
                        self._address, ktype, private=False).get_json()),
            ]
        }
        # prepare the private key bound to address
        if send_private:
            privkey = json.loads(
                self.get_key(self._address, ktype, private=True).get_json())
            privkey.key_data = _encrypt_symmetric(data, passphrase)
            data['keys'].append(privkey)
        headers = None  # TODO: replace for token-based-auth
        self._http_client.request(
            'PUT',
            '/key/%s' % address,
            json.dumps(data),
            headers)

    def get_key(self, address, ktype, private=False):
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
            key = filter(lambda k: isinstance(k, ktype),
                         self._fetch_keys(address))
            if key is None:
                raise KeyNotFound()
            self._wrapper_map[ktype].put_key(key)
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
        self._http_client.request('GET', '/key/%s' % address, None, None)
        keydata = json.loads(self._http_client.read_response())
        leap_assert(
            keydata['address'] == address,
            "Fetched key for wrong address.")
        for key in keydata['keys']:
            # find the key class in the mapper
            keyCLass = filter(
                lambda klass: str(klass) == key['type'],
                self._wrapper_map).pop()
            yield _build_key_from_dict(kClass, address, key)

    def refresh_keys(self):
        """
        Update the user's db of validated keys to see if there are changes.
        """
        raise NotImplementedError(self.refresh_keys)

    def gen_key(self, ktype):
        """
        Generate a key of type C{ktype} bound to the user's address.

        @param ktype: The type of the key.
        @type ktype: KeyType

        @return: The generated key.
        @rtype: EncryptionKey
        """
        return self._wrapper_map[ktype].gen_key(self._address)
