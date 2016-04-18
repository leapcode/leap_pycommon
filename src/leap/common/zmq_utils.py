# -*- coding: utf-8 -*-
# zmq.py
# Copyright (C) 2013, 2014 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Utilities to handle ZMQ certificates.
"""
import os
import logging
import platform
import stat
import shutil

import zmq

try:
    import zmq.auth
except ImportError:
    pass

from leap.common.files import mkdir_p
from leap.common.check import leap_assert

logger = logging.getLogger(__name__)


KEYS_PREFIX = "zmq_certificates"
PUBLIC_KEYS_PREFIX = os.path.join(KEYS_PREFIX, "public_keys")
PRIVATE_KEYS_PREFIX = os.path.join(KEYS_PREFIX, "private_keys")


def zmq_has_curve():
    """
    Return whether the current ZMQ has support for auth and CurveZMQ security.

    :rtype: bool

     Version notes:
       `zmq.curve_keypair()` is new in version 14.0, new in version libzmq-4.0.
            Requires libzmq (>= 4.0) to have been linked with libsodium.
       `zmq.auth` module is new in version 14.1
       `zmq.has()` is new in version 14.1, new in version libzmq-4.1.
    """
    if platform.system() == "Windows":
        # TODO: curve is not working on windows #7919
        return False

    zmq_version = zmq.zmq_version_info()
    pyzmq_version = zmq.pyzmq_version_info()

    if pyzmq_version >= (14, 1, 0) and zmq_version >= (4, 1):
        return zmq.has('curve')

    if pyzmq_version < (14, 1, 0):
        return False

    if zmq_version < (4, 0):
        # security is new in libzmq 4.0
        return False

    try:
        zmq.curve_keypair()
    except zmq.error.ZMQError:
        # security requires libzmq to be linked against libsodium
        return False

    return True


def assert_zmq_has_curve():
    leap_assert(zmq_has_curve, "CurveZMQ not supported!")


def maybe_create_and_get_certificates(basedir, name):
    """
    Generate the needed ZMQ certificates for backend/frontend communication if
    needed.
    """
    assert_zmq_has_curve()
    private_keys_dir = os.path.join(basedir, PRIVATE_KEYS_PREFIX)
    private_key = os.path.join(
        private_keys_dir, name + ".key_secret")
    if not os.path.isfile(private_key):
        mkdir_p(private_keys_dir)
        zmq.auth.create_certificates(private_keys_dir, name)
        # set permissions to: 0700 (U:rwx G:--- O:---)
        os.chmod(private_key, stat.S_IRUSR | stat.S_IWUSR)
        # move public key to public keys directory
        public_keys_dir = os.path.join(basedir, PUBLIC_KEYS_PREFIX)
        old_public_key = os.path.join(
            private_keys_dir, name + ".key")
        new_public_key = os.path.join(
            public_keys_dir, name + ".key")
        mkdir_p(public_keys_dir)
        shutil.move(old_public_key, new_public_key)
    return zmq.auth.load_certificate(private_key)
