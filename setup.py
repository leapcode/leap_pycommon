# -*- coding: utf-8 -*-
# setup.py
# Copyright (C) 2013 LEAP
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
setup file for leap.common
"""
from setuptools import setup, find_packages

# XXX parse pkg/requirements.pip
requirements = [
    "jsonschema",
    "pyxdg",
    'protobuf',
    'protobuf.socketrpc',
    "PyOpenSSL",
    "python-dateutil",
]


dependency_links = [
    "https://protobuf-socket-rpc.googlecode.com/files/protobuf.socketrpc-1.3.2.tar.gz"
]


# XXX add classifiers, docs

setup(
    name='leap.common',
    # If you change version, do it also in
    # src/leap/common/__init__.py
    version='0.2.1-dev',
    url='https://leap.se/',
    license='GPLv3+',
    author='The LEAP Encryption Access Project',
    author_email='info@leap.se',
    description='Common files used by the LEAP Client project.',
    long_description=(
        "Common files used by the LEAP Client project."
    ),
    namespace_packages=["leap"],
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['leap.common.tests']),
    test_suite='leap.common.tests',
    install_requires=requirements,
    dependency_links=dependency_links,
)
