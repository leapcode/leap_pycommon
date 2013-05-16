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

from leap.common.check import leap_assert, leap_assert_type
from leap.common.keymanager.errors import (
    KeyNotFound,
    KeyAlreadyExists,
    KeyAttributesDiffer,
    InvalidSignature,
    EncryptionFailed,
    DecryptionFailed,
    SignFailed,
)
from leap.common.keymanager.keys import (
    EncryptionKey,
    EncryptionScheme,
    is_address,
    keymanager_doc_id,
    build_key_from_dict,
)
from leap.common.keymanager.gpg import GPGWrapper


#
# API functions
#

def encrypt_sym(data, passphrase, sign=None):
    """
    Encrypt C{data} with C{passphrase} and sign with C{sign} private key.

    @param data: The data to be encrypted.
    @type data: str
    @param passphrase: The passphrase used to encrypt C{data}.
    @type passphrase: str
    @param sign: The private key used for signing.
    @type sign: OpenPGPKey

    @return: The encrypted data.
    @rtype: str
    """
    leap_assert_type(passphrase, str)
    if sign is not None:
        leap_assert_type(sign, OpenPGPKey)
        leap_assert(sign.private is True)

    def _encrypt_cb(gpg):
        result = gpg.encrypt(
            data, None,
            sign=sign.key_id if sign else None,
            passphrase=passphrase, symmetric=True)
        # Here we cannot assert for correctness of sig because the sig is in
        # the ciphertext.
        # result.ok    - (bool) indicates if the operation succeeded
        # result.data  - (bool) contains the result of the operation
        if result.ok is False:
            raise EncryptionFailed('Failed to encrypt: %s' % result.stderr)
        return result.data

    return _safe_call(_encrypt_cb, [sign])


def decrypt_sym(data, passphrase, verify=None):
    """
    Decrypt C{data} with C{passphrase} and verify with C{verify} public
    key.

    @param data: The data to be decrypted.
    @type data: str
    @param passphrase: The passphrase used to decrypt C{data}.
    @type passphrase: str
    @param verify: The key used to verify a signature.
    @type verify: OpenPGPKey

    @return: The decrypted data.
    @rtype: str

    @raise InvalidSignature: Raised if unable to verify the signature with
        C{verify} key.
    """
    leap_assert_type(passphrase, str)
    if verify is not None:
        leap_assert_type(verify, OpenPGPKey)
        leap_assert(verify.private is False)

    def _decrypt_cb(gpg):
        result = gpg.decrypt(data, passphrase=passphrase)
        # result.ok    - (bool) indicates if the operation succeeded
        # result.valid - (bool) indicates if the signature was verified
        # result.data  - (bool) contains the result of the operation
        # result.pubkey_fingerpring  - (str) contains the fingerprint of the
        #                              public key that signed this data.
        if result.ok is False:
            raise DecryptionFailed('Failed to decrypt: %s', result.stderr)
        if verify is not None:
            if result.valid is False or \
                    verify.fingerprint != result.pubkey_fingerprint:
                raise InvalidSignature(
                    'Failed to verify signature with key %s: %s' %
                    (verify.key_id, result.stderr))
        return result.data

    return _safe_call(_decrypt_cb, [verify])


def encrypt_asym(data, pubkey, sign=None):
    """
    Encrypt C{data} using public @{key} and sign with C{sign} key.

    @param data: The data to be encrypted.
    @type data: str
    @param pubkey: The key used to encrypt.
    @type pubkey: OpenPGPKey
    @param sign: The key used for signing.
    @type sign: OpenPGPKey

    @return: The encrypted data.
    @rtype: str
    """
    leap_assert_type(pubkey, OpenPGPKey)
    leap_assert(pubkey.private is False, 'Key is not public.')
    if sign is not None:
        leap_assert_type(sign, OpenPGPKey)
        leap_assert(sign.private is True)

    def _encrypt_cb(gpg):
        result = gpg.encrypt(
            data, pubkey.fingerprint,
            sign=sign.key_id if sign else None,
            symmetric=False)
        # Here we cannot assert for correctness of sig because the sig is in
        # the ciphertext.
        # result.ok    - (bool) indicates if the operation succeeded
        # result.data  - (bool) contains the result of the operation
        if result.ok is False:
            raise EncryptionFailed(
                'Failed to encrypt with key %s: %s' %
                (pubkey.key_id, result.stderr))
        return result.data

    return _safe_call(_encrypt_cb, [pubkey, sign])


def decrypt_asym(data, privkey, verify=None):
    """
    Decrypt C{data} using private @{key} and verify with C{verify} key.

    @param data: The data to be decrypted.
    @type data: str
    @param privkey: The key used to decrypt.
    @type privkey: OpenPGPKey
    @param verify: The key used to verify a signature.
    @type verify: OpenPGPKey

    @return: The decrypted data.
    @rtype: str

    @raise InvalidSignature: Raised if unable to verify the signature with
        C{verify} key.
    """
    leap_assert(privkey.private is True, 'Key is not private.')
    if verify is not None:
        leap_assert_type(verify, OpenPGPKey)
        leap_assert(verify.private is False)

    def _decrypt_cb(gpg):
        result = gpg.decrypt(data)
        # result.ok    - (bool) indicates if the operation succeeded
        # result.valid - (bool) indicates if the signature was verified
        # result.data  - (bool) contains the result of the operation
        # result.pubkey_fingerpring  - (str) contains the fingerprint of the
        #                              public key that signed this data.
        if result.ok is False:
            raise DecryptionFailed('Failed to decrypt with key %s: %s' %
                                   (privkey.key_id, result.stderr))
        if verify is not None:
            if result.valid is False or \
                    verify.fingerprint != result.pubkey_fingerprint:
                raise InvalidSignature(
                    'Failed to verify signature with key %s: %s' %
                    (verify.key_id, result.stderr))
        return result.data

    return _safe_call(_decrypt_cb, [privkey, verify])


def is_encrypted(data):
    """
    Return whether C{data} was encrypted using OpenPGP.

    @param data: The data we want to know about.
    @type data: str

    @return: Whether C{data} was encrypted using this wrapper.
    @rtype: bool
    """

    def _is_encrypted_cb(gpg):
        return gpg.is_encrypted(data)

    return _safe_call(_is_encrypted_cb)


def is_encrypted_sym(data):
    """
    Return whether C{data} was encrypted using a public OpenPGP key.

    @param data: The data we want to know about.
    @type data: str

    @return: Whether C{data} was encrypted using this wrapper.
    @rtype: bool
    """

    def _is_encrypted_cb(gpg):
        return gpg.is_encrypted_sym(data)

    return _safe_call(_is_encrypted_cb)


def is_encrypted_asym(data):
    """
    Return whether C{data} was asymmetrically encrypted using OpenPGP.

    @param data: The data we want to know about.
    @type data: str

    @return: Whether C{data} was encrypted using this wrapper.
    @rtype: bool
    """

    def _is_encrypted_cb(gpg):
        return gpg.is_encrypted_asym(data)

    return _safe_call(_is_encrypted_cb)


def sign(data, privkey):
    """
    Sign C{data} with C{privkey}.

    @param data: The data to be signed.
    @type data: str
    @param privkey: The private key to be used to sign.
    @type privkey: OpenPGPKey

    @return: The ascii-armored signed data.
    @rtype: str
    """
    leap_assert_type(privkey, OpenPGPKey)
    leap_assert(privkey.private is True)

    def _sign_cb(gpg):
        result = gpg.sign(data, keyid=privkey.key_id)
        # result.fingerprint - contains the fingerprint of the key used to
        #                      sign.
        if result.fingerprint is None:
            raise SignFailed(
                'Failed to sign with key %s: %s' %
                (privkey.key_id, result.stderr))
        leap_assert(
            result.fingerprint == privkey.fingerprint,
            'Signature and private key fingerprints mismatch: %s != %s' %
            (result.fingerprint, privkey.fingerprint))
        return result.data

    return _safe_call(_sign_cb, [privkey])


def verify(data, pubkey):
    """
    Verify signed C{data} with C{pubkey}.

    @param data: The data to be verified.
    @type data: str
    @param pubkey: The public key to be used on verification.
    @type pubkey: OpenPGPKey

    @return: The ascii-armored signed data.
    @rtype: str
    """
    leap_assert_type(pubkey, OpenPGPKey)
    leap_assert(pubkey.private is False)

    def _verify_cb(gpg):
        result = gpg.verify(data)
        if result.valid is False or \
                result.fingerprint != pubkey.fingerprint:
            raise InvalidSignature(
                'Failed to verify signature with key %s.' % pubkey.key_id)
        return True

    return _safe_call(_verify_cb, [pubkey])


#
# Helper functions
#

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


def _build_keyring(keys=[]):
    """

    Create an empty GPG keyring and import C{keys} into it.

    @param keys: List of keys to add to the keyring.
    @type keys: list of OpenPGPKey

    @return: A GPG wrapper with a unitary keyring.
    @rtype: gnupg.GPG
    """
    privkeys = filter(lambda key: key.private is True, keys)
    pubkeys = filter(lambda key: key.private is False, keys)
    # here we filter out public keys that have a correspondent private key in
    # the list because the private key_data by itself is enough to also have
    # the public key in the keyring, and we want to count the keys afterwards.
    privaddrs = map(lambda privkey: privkey.address, privkeys)
    pubkeys = filter(lambda pubkey: pubkey.address not in privaddrs, pubkeys)
    # create temporary dir for temporary gpg keyring
    tmpdir = tempfile.mkdtemp()
    gpg = GPGWrapper(gnupghome=tmpdir)
    leap_assert(len(gpg.list_keys()) is 0, 'Keyring not empty.')
    # import keys into the keyring
    gpg.import_keys(
        reduce(
            lambda x, y: x+y,
            [key.key_data for key in pubkeys+privkeys], ''))
    # assert the number of keys in the keyring
    leap_assert(
        len(gpg.list_keys()) == len(pubkeys)+len(privkeys),
        'Wrong number of public keys in keyring: %d, should be %d)' %
        (len(gpg.list_keys()), len(pubkeys)+len(privkeys)))
    leap_assert(
        len(gpg.list_keys(secret=True)) == len(privkeys),
        'Wrong number of private keys in keyring: %d, should be %d)' %
        (len(gpg.list_keys(secret=True)), len(privkeys)))
    return gpg


def _destroy_keyring(gpg):
    """
    Securely erase a keyring.

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


def _safe_call(callback, keys=[]):
    """
    Run C{callback} over a keyring containing C{keys}.

    @param callback: Function whose first argument is the gpg keyring.
    @type callback: function(gnupg.GPG)
    @param keys: List of keys to add to the keyring.
    @type keys: list of OpenPGPKey

    @return: The results of the callback.
    @rtype: str or bool
    """
    gpg = _build_keyring(filter(lambda key: key is not None, keys))
    val = callback(gpg)
    _destroy_keyring(gpg)
    return val


#
# The OpenPGP wrapper
#

class OpenPGPKey(EncryptionKey):
    """
    Base class for OpenPGP keys.
    """


class OpenPGPScheme(EncryptionScheme):
    """
    A wrapper for OpenPGP keys.
    """

    def __init__(self, soledad):
        """
        Initialize the OpenPGP wrapper.

        @param soledad: A Soledad instance for key storage.
        @type soledad: leap.soledad.Soledad
        """
        EncryptionScheme.__init__(self, soledad)

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
        leap_assert(is_address(address), 'Not an user address: %s' % address)
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
            # insert both public and private keys in storage
            for secret in [True, False]:
                key = gpg.list_keys(secret=secret).pop()
                openpgp_key = _build_key_from_gpg(
                    address, key,
                    gpg.export_keys(key['fingerprint'], secret=secret))
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
        leap_assert(is_address(address), 'Not an user address: %s' % address)
        doc = self._get_key_doc(address, private)
        if doc is None:
            raise KeyNotFound(address)
        return build_key_from_dict(OpenPGPKey, address, doc.content)

    def put_ascii_key(self, key_data):
        """
        Put key contained in ascii-armored C{key_data} in local storage.

        @param key_data: The key data to be stored.
        @type key_data: str
        """
        leap_assert_type(key_data, str)

        def _put_ascii_key_cb(gpg):
            gpg.import_keys(key_data)
            privkey = None
            pubkey = None
            try:
                privkey = gpg.list_keys(secret=True).pop()
            except IndexError:
                pass
            pubkey = gpg.list_keys(secret=False).pop()  # unitary keyring
            # extract adress from first uid on key
            match = re.match('.*<([\w.-]+@[\w.-]+)>.*', pubkey['uids'].pop())
            leap_assert(match is not None, 'No user address in key data.')
            address = match.group(1)
            if privkey is not None:
                match = re.match(
                    '.*<([\w.-]+@[\w.-]+)>.*', privkey['uids'].pop())
                leap_assert(match is not None, 'No user address in key data.')
                privaddress = match.group(1)
                leap_assert(
                    address == privaddress,
                    'Addresses in pub and priv key differ.')
                leap_assert(
                    pubkey['fingerprint'] == privkey['fingerprint'],
                    'Fingerprints for pub and priv key differ.')
                # insert private key in storage
                openpgp_privkey = _build_key_from_gpg(
                    address, privkey,
                    gpg.export_keys(privkey['fingerprint'], secret=True))
                self.put_key(openpgp_privkey)
            # insert public key in storage
            openpgp_pubkey = _build_key_from_gpg(
                address, pubkey,
                gpg.export_keys(pubkey['fingerprint'], secret=False))
            self.put_key(openpgp_pubkey)

        _safe_call(_put_ascii_key_cb)

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
                doc_id=keymanager_doc_id(
                    OpenPGPKey, key.address, key.private))
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
        return self._soledad.get_doc(
            keymanager_doc_id(OpenPGPKey, address, private))

    def delete_key(self, key):
        """
        Remove C{key} from storage.

        @param key: The key to be removed.
        @type key: EncryptionKey
        """
        leap_assert(key.__class__ is OpenPGPKey, 'Wrong key type.')
        stored_key = self.get_key(key.address, private=key.private)
        if stored_key is None:
            raise KeyNotFound(key)
        if stored_key.__dict__ != key.__dict__:
            raise KeyAttributesDiffer(key)
        doc = self._soledad.get_doc(
            keymanager_doc_id(OpenPGPKey, key.address, key.private))
        self._soledad.delete_doc(doc)
