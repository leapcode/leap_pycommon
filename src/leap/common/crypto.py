# -*- coding: utf-8 -*-
# crypto.py
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


from Crypto.Cipher import AES
from Crypto.Random import random
from Crypto.Util import Counter
from leap.common.check import leap_assert, leap_assert_type


#
# encryption methods
#

class EncryptionMethods(object):
    """
    Representation of encryption methods that can be used.
    """

    AES_256_CTR = 'aes-256-ctr'


class UnknownEncryptionMethod(Exception):
    """
    Raised when trying to encrypt/decrypt with unknown method.
    """
    pass


#
# encrypt/decrypt functions
#

# In the future, we might want to implement other encryption schemes and
# possibly factor out the actual encryption/decryption routines of the
# following functions to specific classes, while not changing the API.

def encrypt_sym(data, key, method=EncryptionMethods.AES_256_CTR):
    """
    Encrypt C{data} with C{key}, using C{method} encryption method.

    @param data: The data to be encrypted.
    @type data: str
    @param key: The key used to encrypt C{data} (must be 256 bits long).
    @type key: str
    @param method: The encryption method to use.
    @type method: str

    @return: A tuple with the initial value and the encrypted data.
    @rtype: (long, str)
    """
    leap_assert_type(key, str)

    # AES-256 in CTR mode
    if method == EncryptionMethods.AES_256_CTR:
        leap_assert(
            len(key) == 32,  # 32 x 8 = 256 bits.
            'Wrong key size: %s bits (must be 256 bits long).' % (len(key)*8))
        iv = random.getrandbits(256)
        ctr = Counter.new(128, initial_value=iv)
        cipher = AES.new(key=key, mode=AES.MODE_CTR, counter=ctr)
        return iv, cipher.encrypt(data)

    # raise if method is unknown
    raise UnknownEncryptionMethod('Unkwnown method: %s' % method)


def decrypt_sym(data, key, method=EncryptionMethods.AES_256_CTR, **kwargs):
    """
    Decrypt C{data} with C{key} using C{method} encryption method.

    @param data: The data to be decrypted with prepended IV.
    @type data: str
    @param key: The key used to decrypt C{data} (must be 256 bits long).
    @type key: str
    @param method: The encryption method to use.
    @type method: str
    @param kwargs: Other parameters specific to each encryption method.
    @type kwargs: long

    @return: The decrypted data.
    @rtype: str
    """
    leap_assert_type(key, str)

    # AES-256 in CTR mode
    if method == EncryptionMethods.AES_256_CTR:
        # assert params
        leap_assert(
            len(key) == 32,  # 32 x 8 = 256 bits.
            'Wrong key size: %s (must be 256 bits long).' % len(key))
        leap_assert(
            'iv' in kwargs,
            'AES-256-CTR needs an initial value given as.')
        ctr = Counter.new(128, initial_value=kwargs['iv'])
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        return cipher.decrypt(data)

    # raise if method is unknown
    raise UnknownEncryptionMethod('Unkwnown method: %s' % method)
