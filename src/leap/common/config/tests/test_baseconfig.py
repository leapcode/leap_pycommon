# -*- coding: utf-8 -*-
# test_baseconfig.py
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
Tests for baseconfig
"""
import json
import unittest
import copy

from leap.common.config.baseconfig import BaseConfig, LocalizedKey
from leap.common.testing.basetest import BaseLeapTest

from mock import Mock

# reduced eipconfig sample config
sample_config = {
    "gateways": [
    {
        "capabilities": {
            "adblock": False,
            "transport": ["openvpn"],
            "user_ips": False
        },
        "host": "host.dev.example.org",
    }, {
        "capabilities": {
            "adblock": False,
            "transport": ["openvpn"],
            "user_ips": False
        },
        "host": "host2.dev.example.org",
    }
    ],
    "default_language": "en",
    "languages": [
        "en",
        "es"
    ],
    "name": {
        "en": "Baseconfig testing environment",
        "es": "Entorno de pruebas de Baseconfig"
    },
    "serial": 1,
    "version": 1
}

# reduced eipconfig.spec version
sample_spec = {
    'description': 'sample eip service config',
    'type': 'object',
    'properties': {
        'serial': {
            'type': int,
            'default': 1,
            'required': ["True"]
        },
        'version': {
            'type': int,
            'default': 1,
            'required': ["True"]
        },
        "default_language": {
            'type': unicode,
            'default': 'en'
        },
        'languages': {
            'type': list,
            'default': ['en']
        },
        'name': {
            'type': dict,
            'format': 'translatable',
            'default': {u'en': u'Test Provider'}
        },
        'gateways': {
            'type': list,
            'default': [
                {"capabilities": {
                    "adblock": True,
                    "transport": ["openvpn"],
                    "user_ips": False},
                 "host": "location.example.org",
                 }]
        },
    }
}


class TestConfig(BaseConfig):
    """
    BaseConfig implementation for testing purposes only.
    """
    def get_gateways(self):
        return self._safe_get_value("gateways")

    def get_serial(self):
        return self._safe_get_value("serial")

    def get_version(self):
        return self._safe_get_value("version")

    def _get_schema(self):
        return sample_spec

    def _get_spec(self):
        return self._get_schema()

    def get_default_language(self):
        return self._safe_get_value("default_language")

    @LocalizedKey
    def get_name(self):
        return self._safe_get_value("name")


class BaseConfigTest(BaseLeapTest):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _write_config(self, data):
        """
        Helper to write some data to a temp config file.

        :param data: data to be used to save in the config file.
        :data type: dict (valid json)
        """
        self.config_file = self.get_tempfile("config.json")
        conf = open(self.config_file, "w")
        conf.write(json.dumps(data))
        conf.close()

    def _get_config(self, fromfile=False, data=sample_config):
        """
        Helper that returns a TestConfig object using the data parameter
        or a sample data.

        :param fromfile: sets if we should use a file or a string
        :fromfile type: bool
        :param data: sets the data to be used to load in the TestConfig object
        :data type: dict (valid json)
        :rtype: TestConfig
        """
        config = TestConfig()

        loaded = False
        if fromfile:
            self._write_config(data)
            loaded = config.load(self.config_file, relative=False)
        else:
            json_string = json.dumps(data)
            loaded = config.load(data=json_string)

        if not loaded:
            return None

        return config

    def test_loads_from_file(self):
        config = self._get_config(fromfile=True)
        self.assertIsNotNone(config)

    def test_loads_from_data(self):
        config = self._get_config()
        self.assertIsNotNone(config)

    def test_load_valid_config_from_file(self):
        config = self._get_config(fromfile=True)
        self.assertIsNotNone(config)

        self.assertEqual(config.get_version(), sample_config["version"])
        self.assertEqual(config.get_serial(), sample_config["serial"])
        self.assertEqual(config.get_gateways(), sample_config["gateways"])

    def test_load_valid_config_from_data(self):
        config = self._get_config()
        self.assertIsNotNone(config)

        self.assertEqual(config.get_version(), sample_config["version"])
        self.assertEqual(config.get_serial(), sample_config["serial"])
        self.assertEqual(config.get_gateways(), sample_config["gateways"])

    def test_safe_get_value_no_config(self):
        config = TestConfig()

        with self.assertRaises(AssertionError):
            config.get_version()

    def test_safe_get_value_non_existent_value(self):
        config = self._get_config()

        self.assertIsNone(config._safe_get_value('non-existent-value'))

    def test_loaded(self):
        config = self._get_config()
        self.assertTrue(config.loaded())

    def test_not_loaded(self):
        config = TestConfig()
        self.assertFalse(config.loaded())

    def test_save_and_load(self):
        config = self._get_config()
        config.get_path_prefix = Mock(return_value=self.tempdir)
        config_file = 'test_config.json'
        self.assertTrue(config.save([config_file]))

        config_saved = TestConfig()
        config_file_path = self.get_tempfile(config_file)
        self.assertTrue(config_saved.load(config_file_path, relative=False))

        self.assertEqual(config.get_version(), config_saved.get_version())
        self.assertEqual(config.get_serial(), config_saved.get_serial())
        self.assertEqual(config.get_gateways(), config_saved.get_gateways())

    def test_localizations(self):
        conf = self._get_config()

        self.assertEqual(conf.get_name(lang='en'), sample_config['name']['en'])
        self.assertEqual(conf.get_name(lang='es'), sample_config['name']['es'])

    def _localized_config(self, lang):
        """
        Helper to change default language of the provider config.
        """
        conf = copy.deepcopy(sample_config)
        conf['default_language'] = lang
        json_string = json.dumps(conf)
        config = TestConfig()
        config.load(data=json_string)

        return config

    def test_default_localization1(self):
        default_language = sample_config['languages'][0]
        config = self._localized_config(default_language)

        default_name = sample_config['name'][default_language]

        self.assertEqual(config.get_name(lang='xx'), default_name)
        self.assertEqual(config.get_name(), default_name)

    def test_default_localization2(self):
        default_language = sample_config['languages'][1]
        config = self._localized_config(default_language)

        default_name = sample_config['name'][default_language]

        self.assertEqual(config.get_name(lang='xx'), default_name)
        self.assertEqual(config.get_name(), default_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
