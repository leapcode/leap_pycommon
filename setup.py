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

from pkg import utils
parsed_reqs = utils.parse_requirements()

import versioneer
versioneer.versionfile_source = 'src/leap/common/_version.py'
versioneer.versionfile_build = 'leap/common/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'leap.common-'

tests_requirements = [
    'mock',
]

trove_classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    ("License :: OSI Approved :: GNU General "
     "Public License v3 or later (GPLv3+)"),
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: Communications",
    "Topic :: Security",
    "Topic :: Utilities"
]

setup(
    name='leap.common',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url='https://leap.se/',
    license='GPLv3+',
    author='The LEAP Encryption Access Project',
    author_email='info@leap.se',
    description='Common files used by the LEAP project.',
    long_description=(
        "Common files used by the LEAP Client project."
    ),
    classifiers=trove_classifiers,
    namespace_packages=["leap"],
    package_dir={'': 'src'},
    # For now, we do not exclude tests because of the circular dependency
    # between leap.common and leap.soledad.
    #packages=find_packages('src', exclude=['leap.common.tests']),
    packages=find_packages('src'),
    test_suite='leap.common.tests',
    install_requires=parsed_reqs,
    #dependency_links=dependency_links,
    tests_require=tests_requirements,
    include_package_data=True
)
