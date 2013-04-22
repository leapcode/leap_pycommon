# -*- coding: utf-8 -*-
# openpgp.py
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
Infrastructure for using OpenPGP keys in Key Manager.
"""


import re
import tempfile
import shutil

from leap.common.check import leap_assert
from leap.common.keymanager.errors import (
    KeyNotFound,
    KeyAlreadyExists,
)
from leap.common.keymanager.keys import (
    EncryptionKey,
    KeyTypeWrapper,
)
from leap.common.keymanager.gpg import GPGWrapper
from leap.common.keymanager.util import (
    _is_address,
    _build_key_from_doc,
    _keymanager_doc_id,
)


#
# Utility functions
#

def _encrypt_symmetric(data, password):
    """
    Encrypt C{data} with C{password}.

    This function uses the OpenPGP wrapper to perform the encryption.

    @param data: The data to be encrypted.
    @type data: str
    @param password: The password used to encrypt C{data}.
    @type password: str
    @return: The encrypted data.
    @rtype: str
    """
    cyphertext = None

    def _encrypt_cb(gpg):
        cyphertext = str(
            gpg.encrypt(
                data, None, passphrase=password, symmetric=True))
        data['keys'].append(privkey)

    _safe_call(_encrypt_cb)
    return cyphertext


def _build_key_from_gpg(address, key, key_data):
    """
    Build an OpenPGPKey for C{address} based on C{key} from
    local gpg storage.

    ASCII armored GPG key data has to be queried independently in this
    wrapper, so we receive it in C{key_data}.

    @param address: The address bound to the key.
    @type address: str
    @param key: Key obtained from GPG storage.
    @type key: dict
    @param key_data: Key data obtained from GPG storage.
    @type key_data: str
    @return: An instance of the key.
    @rtype: OpenPGPKey
    """
    return OpenPGPKey(
        address,
        key_id=key['keyid'],
        fingerprint=key['fingerprint'],
        key_data=key_data,
        private=True if key['type'] == 'sec' else False,
        length=key['length'],
        expiry_date=key['expires'],
        validation=None,  # TODO: verify for validation.
    )


def _build_unitary_gpgwrapper(key_data=None):
    """
    Return a temporary GPG wrapper keyring containing exactly zero or one
    keys.

    Temporary unitary keyrings allow the to use GPG's facilities for exactly
    one key. This function creates an empty temporary keyring and imports
    C{key_data} if it is not None.

    @param key_data: ASCII armored key data.
    @type key_data: str
    @return: A GPG wrapper with a unitary keyring.
    @rtype: gnupg.GPG
    """
    tmpdir = tempfile.mkdtemp()
    gpg = GPGWrapper(gnupghome=tmpdir)
    leap_assert(len(gpg.list_keys()) is 0, 'Keyring not empty.')
    if key_data:
        gpg.import_keys(key_data)
        leap_assert(
            len(gpg.list_keys()) is 1,
            'Unitary keyring has wrong number of keys: %d.'
            % len(gpg.list_keys()))
    return gpg


def _destroy_unitary_gpgwrapper(gpg):
    """
    Securely erase a unitary keyring.

    @param gpg: A GPG wrapper instance.
    @type gpg: gnupg.GPG
    """
    for secret in [True, False]:
        for key in gpg.list_keys(secret=secret):
            gpg.delete_keys(
                key['fingerprint'],
                secret=secret)
    leap_assert(len(gpg.list_keys()) is 0, 'Keyring not empty!')
    # TODO: implement some kind of wiping of data or a more secure way that
    # does not write to disk.
    shutil.rmtree(gpg.gnupghome)


def _safe_call(callback, key_data=None, **kwargs):
    """
    Run C{callback} in an unitary keyring containing C{key_data}.

    @param callback: Function whose first argument is the gpg keyring.
    @type callback: function(gnupg.GPG)
    @param key_data: ASCII armored key data.
    @type key_data: str
    @param **kwargs: Other eventual parameters for the callback.
    @type **kwargs: **dict
    """
    gpg = _build_unitary_gpgwrapper(key_data)
    callback(gpg, **kwargs)
    _destroy_unitary_gpgwrapper(gpg)


#
# The OpenPGP wrapper
#

class OpenPGPKey(EncryptionKey):
    """
    Base class for OpenPGP keys.
    """


class OpenPGPWrapper(KeyTypeWrapper):
    """
    A wrapper for OpenPGP keys.
    """

    def __init__(self, soledad):
        """
        Initialize the OpenPGP wrapper.

        @param soledad: A Soledad instance for key storage.
        @type soledad: leap.soledad.Soledad
        """
        KeyTypeWrapper.__init__(self, soledad)
        self._soledad = soledad

    def gen_key(self, address):
        """
        Generate an OpenPGP keypair bound to C{address}.

        @param address: The address bound to the key.
        @type address: str
        @return: The key bound to C{address}.
        @rtype: OpenPGPKey
        @raise KeyAlreadyExists: If key already exists in local database.
        """
        # make sure the key does not already exist
        leap_assert(_is_address(address), 'Not an user address: %s' % address)
        try:
            self.get_key(address)
            raise KeyAlreadyExists(address)
        except KeyNotFound:
            pass

        def _gen_key_cb(gpg):
            params = gpg.gen_key_input(
                key_type='RSA',
                key_length=4096,
                name_real=address,
                name_email=address,
                name_comment='Generated by LEAP Key Manager.')
            gpg.gen_key(params)
            pubkeys = gpg.list_keys()
            # assert for new key characteristics
            leap_assert(
                len(pubkeys) is 1,  # a unitary keyring!
                'Keyring has wrong number of keys: %d.' % len(pubkeys))
            key = gpg.list_keys(secret=True).pop()
            leap_assert(
                len(key['uids']) is 1,  # with just one uid!
                'Wrong number of uids for key: %d.' % len(key['uids']))
            leap_assert(
                re.match('.*<%s>$' % address, key['uids'][0]) is not None,
                'Key not correctly bound to address.')
            openpgp_key = _build_key_from_gpg(
                address, key,
                gpg.export_keys(key['fingerprint']))
            self.put_key(openpgp_key)

        _safe_call(_gen_key_cb)
        return self.get_key(address, private=True)

    def get_key(self, address, private=False):
        """
        Get key bound to C{address} from local storage.

        @param address: The address bound to the key.
        @type address: str
        @param private: Look for a private key instead of a public one?
        @type private: bool

        @return: The key bound to C{address}.
        @rtype: OpenPGPKey
        @raise KeyNotFound: If the key was not found on local storage.
        """
        leap_assert(_is_address(address), 'Not an user address: %s' % address)
        doc = self._get_key_doc(address, private)
        if doc is None:
            raise KeyNotFound(address)
        return _build_key_from_doc(OpenPGPKey, address, doc)

    def put_key_raw(self, data):
        """
        Put key contained in raw C{data} in local storage.

        @param data: The key data to be stored.
        @type data: str
        """
        # TODO: add more checks for correct key data.
        leap_assert(data is not None, 'Data does not represent a key.')

        def _put_key_raw_cb(gpg):

            key = gpg.list_keys(secret=False).pop()  # unitary keyring
            # extract adress from first uid on key
            match = re.match('.*<([\w.-]+@[\w.-]+)>.*', key['uids'].pop())
            leap_assert(match is not None, 'No user address in key data.')
            address = match.group(1)
            openpgp_key = _build_key_from_gpg(
                address, key,
                gpg.export_keys(key['fingerprint']))
            self.put_key(openpgp_key)

        _safe_call(_put_key_raw_cb, data)

    def put_key(self, key):
        """
        Put C{key} in local storage.

        @param key: The key to be stored.
        @type key: OpenPGPKey
        """
        doc = self._get_key_doc(key.address, private=key.private)
        if doc is None:
            self._soledad.create_doc_from_json(
                key.get_json(),
                doc_id=_keymanager_doc_id(key.address, key.private))
        else:
            doc.set_json(key.get_json())
            self._soledad.put_doc(doc)

    def _get_key_doc(self, address, private=False):
        """
        Get the document with a key (public, by default) bound to C{address}.

        If C{private} is True, looks for a private key instead of a public.

        @param address: The address bound to the key.
        @type address: str
        @param private: Whether to look for a private key.
        @type private: bool
        @return: The document with the key or None if it does not exist.
        @rtype: leap.soledad.backends.leap_backend.LeapDocument
        """
        return self._soledad.get_doc(_keymanager_doc_id(address, private))
