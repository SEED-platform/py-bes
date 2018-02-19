#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved.
..codeauthor::Fable Turas <fable@raintechpdx.com>

pybes.utils unit tests
"""

# Imports from Standard Library
import sys
from unittest import TestCase

# Local Imports
from pybes.pybes import APIError, BESClient
from pybes.utils.bes_preview import (
    _create_bes_preview_payload,
    _validate_bes_payload,
    create_bes_preview_bldg_from_seed,
    get_bes_preview_report,
    initiate_preview_simulation,
)

PY3 = sys.version_info[0] == 3
if PY3:
    from unittest import mock
else:
    import mock
# Constants

BASE_URL = 'https://api.labworks.org/api'
# Helper Functions & Classes

# Tests


class GBRBESTests(TestCase):
    """Unit tests for pybes.utils functions"""

    def setUp(self):
        """setUp"""
        self.mock_view = {
            'id': 1,
            'property': 1,
            'cycle': 1,
            'state': {
                'year_built': 1955,
                'property_type': 'Retail',
                'property_name': 'Test Property',
                'gross_floor_area': 10000.0,
                'address_line_1': '123 Main',
                'city': 'Boring',
                'state': 'OR',
                'postal_code': '97209',
                'extra_data': {
                    'number_floors': 1
                }
            }
        }
        self.mock_bes = {
            'status!': 'Rated',
            'address': '123 Main',
            'city': 'Boring',
            'state': 'OR',
            'zip_code': '97209',
        }
        self.client = BESClient(base_url=BASE_URL)

    @mock.patch('pybes.utils.bes_preview.convert_bes_year')
    @mock.patch('pybes.utils.bes_preview.get_bes_property_type')
    def test_create_bes_preview_payload(self, mock_bes_type, mock_bes_year):
        """Test _create_bes_preview_payload"""
        mock_bes_type.return_value = 'Retail'
        mock_bes_year.return_value = 1955
        result = _create_bes_preview_payload(self.mock_view)
        mock_bes_type.assert_called_with(
            self.mock_view['state']['property_type']
        )
        mock_bes_year.assert_called_with(self.mock_view['state']['year_built'])
        self.assertEqual('Real', result['assessment_type'])

    def test_validate_bes_payload(self):
        """Test _validate_bes_payload"""
        payload = _create_bes_preview_payload(self.mock_view)
        self.assertTrue(_validate_bes_payload(payload))

        self.assertFalse(_validate_bes_payload({}))

    @mock.patch('pybes.utils.bes_preview._create_bes_preview_payload')
    @mock.patch('pybes.utils.bes_preview._validate_bes_payload')
    @mock.patch('pybes.utils.bes_preview.BESClient.create_preview_building')
    def test_create_bes_preview_building_from_seed(self, mock_create_method,
                                                   mock_validate,
                                                   mock_payload):
        """Test create_bes_preview_bldg_from_seed"""
        mock_payload.return_value = {}
        mock_validate.return_value = False
        mock_create_method.return_value = {}
        with self.assertRaises(ValueError):
            create_bes_preview_bldg_from_seed(self.client, {})

        mock_validate.return_value = True
        create_bes_preview_bldg_from_seed(self.client, {})
        self.assertTrue(mock_create_method.called)

    @mock.patch('pybes.utils.bes_preview.BESClient.validate_preview_building')
    @mock.patch('pybes.utils.bes_preview.BESClient.simulate_preview_building')
    @mock.patch('pybes.utils.bes_preview.BESClient.get_preview_building')
    def test_initiate_bes_simulation(self, mock_get_building, mock_simulate,
                                     mock_validate):
        """Test initiate_preview_simulation"""
        with self.assertRaises(ValueError):
            initiate_preview_simulation(self.client, None)
        with self.assertRaises(ValueError):
            initiate_preview_simulation(self.client, '10')

        mock_validate.return_value = True
        mock_simulate.return_value = None
        mock_get_building.return_value = {'status!': 'Running'}
        result = initiate_preview_simulation(self.client, 1)
        expected = 'Running'
        self.assertEqual(result, expected)

    @mock.patch('pybes.utils.bes_preview.initiate_preview_simulation')
    @mock.patch('pybes.utils.bes_preview.BESClient.get_building')
    @mock.patch('pybes.utils.bes_preview.BESClient.get_preview_building')
    def test_get_bes_preview_report(self, mock_get_preview_bldg, mock_get_bldg,
                                    mock_simulation):
        """Test get_bes_preview_report"""
        mock_get_bldg.return_value = {}
        mock_get_preview_bldg.return_value = {'status!': 'Running'}
        mock_simulation.return_value = {'status!': 'Running'}

        get_bes_preview_report(self.client, 1)
        self.assertFalse(mock_get_bldg.called)

        mock_get_preview_bldg.return_value = {'status!': 'Rated'}
        get_bes_preview_report(self.client, 1, 'Running')
        self.assertFalse(mock_get_bldg.called)

        get_bes_preview_report(self.client, 1, 'Editing')
        self.assertTrue(mock_simulation.called)

        get_bes_preview_report(self.client, 1)
        self.assertTrue(mock_get_bldg.called)
