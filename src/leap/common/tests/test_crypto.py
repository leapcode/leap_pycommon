## -*- coding: utf-8 -*-
# test_crypto.py
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
Tests for the crypto submodule.
"""


import os
import binascii


from leap.common.testing.basetest import BaseLeapTest
from leap.common import crypto
from Crypto import Random


class CryptoTestCase(BaseLeapTest):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_encrypt_decrypt_sym(self):
        # generate 256-bit key
        key = Random.new().read(32)
        iv, cyphertext = crypto.encrypt_sym(
            'data', key,
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertTrue(cyphertext is not None)
        self.assertTrue(cyphertext != '')
        self.assertTrue(cyphertext != 'data')
        plaintext = crypto.decrypt_sym(
            cyphertext, key, iv=iv,
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertEqual('data', plaintext)

    def test_decrypt_with_wrong_iv_fails(self):
        key = Random.new().read(32)
        iv, cyphertext = crypto.encrypt_sym(
            'data', key,
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertTrue(cyphertext is not None)
        self.assertTrue(cyphertext != '')
        self.assertTrue(cyphertext != 'data')
        # get a different iv by changing the first byte
        rawiv = binascii.a2b_base64(iv)
        wrongiv = rawiv
        while wrongiv == rawiv:
            wrongiv = os.urandom(1) + rawiv[1:]
        plaintext = crypto.decrypt_sym(
            cyphertext, key, iv=binascii.b2a_base64(wrongiv),
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertNotEqual('data', plaintext)

    def test_decrypt_with_wrong_key_fails(self):
        key = Random.new().read(32)
        iv, cyphertext = crypto.encrypt_sym(
            'data', key,
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertTrue(cyphertext is not None)
        self.assertTrue(cyphertext != '')
        self.assertTrue(cyphertext != 'data')
        wrongkey = Random.new().read(32)  # 256-bits key
        # ensure keys are different in case we are extremely lucky
        while wrongkey == key:
            wrongkey = Random.new().read(32)
        plaintext = crypto.decrypt_sym(
            cyphertext, wrongkey, iv=iv,
            method=crypto.EncryptionMethods.AES_256_CTR)
        self.assertNotEqual('data', plaintext)
