#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved.
..codeauthor::Fable Turas <fable@raintechpdx.com>

Unit tests for pybes.utils/bes_full.py
"""

# Imports from Standard Library
import sys
from unittest import TestCase

# Local Imports
from pybes.pybes import BESClient
from pybes.utils.bes_full import (
    _get_full_bldg_pdf_url,
    _get_property_type,
    get_bes_buildings,
    get_bes_full_report,
    initiate_full_simulation,
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

class BESFullTests(TestCase):
    """Unit tests for bes_full"""

    def setUp(self):
        """setUp"""
        use_types = [{
            u'cooling_set_point': u'75.0',
            u'created_at': u'2017-06-07T09:05:30-07:00',
            u'display_name': u'Office',
            u'heating_set_point': u'70.0',
            u'id': 4,
            u'maximum_lpd': 1.2999999523162842,
            u'minimum_lpd': 0.6000000238418579,
            u'misc_energy_loads': u'0.75',
            u'operating_hours_per_week': u'48.6',
            u'score_type_id': 7,
            u'service_name': u'office',
            u'sq_ft_per_occ': 200,
            u'updated_at': u'2017-06-07T09:05:30-07:00',
            u'weather_coefficient_type_id': 1
        }]

        self.mock_building = {
            'address': '123 Main',
            'city': 'Boring',
            'state': 'OR',
            'zip_code': '97209',
            'id': 1111,
            'name': 'Test Building',
            'status_type_id': 3,
            'year_of_construction': 1955,
            'total_floor_area': 10000,
            'use_types': use_types,
            'floors': []
        }
        self.client = BESClient(base_url=BASE_URL)
        self.status_map = {
            1: 'Editing', 2: 'Running', 3: 'Rated', 4: 'Submitted'
        }

    def test_get_full_bldg_pdf_url(self):
        """Test _get_full_bldg_pdf_url"""
        result = _get_full_bldg_pdf_url(1, 'http://baseurl.xx/api')
        expected = 'http://baseurl.xx/buildings/1/report.pdf'
        self.assertTrue(result, expected)

    def test_get_property_type(self):
        """Test _get_property_type"""
        result = _get_property_type(self.mock_building)
        expected = 'Office'
        self.assertEqual(result, expected)

    @mock.patch('pybes.utils.bes_full.BESClient.simulate_building')
    @mock.patch('pybes.utils.bes_full.BESClient.validate_building')
    @mock.patch('pybes.utils.bes_full.BESClient.get_building')
    def test_initiate_full_simulation(self, mock_get, mock_validate,
                                      mock_simulate):
        """Test initiate_full_simulation"""
        self.assertRaises(
            ValueError,
            initiate_full_simulation,
            self.client, None, status_map=self.status_map
        )
        mock_simulate.return_value = None
        mock_validate.return_value = None
        mock_get.return_value = self.mock_building
        result = initiate_full_simulation(
            self.client, 1, status_map=self.status_map
        )
        expected = 'Rated'
        self.assertTrue(result, expected)

    @mock.patch('pybes.utils.bes_full.initiate_full_simulation')
    @mock.patch('pybes.utils.bes_full._get_full_bldg_pdf_url')
    @mock.patch('pybes.utils.bes_full._get_property_type')
    @mock.patch('pybes.utils.bes_full.BESClient.get_building_score')
    def test_get_bes_full_report(self, mock_score, mock_get_type, mock_pdf_url,
                                 mock_initiate):
        """Test get_bes_full_report"""
        mock_pdf_url.return_value = 'testapi/buildings/111/report.pdf'
        mock_get_type.return_value = 'Office'
        mock_score.return_value = {}
        result, status = get_bes_full_report(
            self.client, self.mock_building, status_map=self.status_map,
            base_url=BASE_URL
        )
        self.assertIn('pdf_url', result.keys())
        self.assertEqual(result['bes_type'], 'Full')

        mock_initiate.return_value = 'Running'
        unrated = {'id': 112, 'status_type_id': 1, 'floors': []}
        result, status = get_bes_full_report(
            self.client, unrated, status_map=self.status_map
        )
        self.assertTrue(mock_initiate.called)
        self.assertIsNone(result)

    @mock.patch('pybes.utils.bes_full.BESClient.get_preview_building')
    @mock.patch('pybes.utils.bes_full.BESClient.get_building')
    @mock.patch('pybes.utils.bes_full.BESClient.list_buildings')
    @mock.patch('pybes.utils.bes_full.BESClient.list_preview_buildings')
    @mock.patch('pybes.utils.bes_full.get_bes_preview_report')
    @mock.patch('pybes.utils.bes_full.get_bes_full_report')
    def test_get_bes_buildings(self, mock_full_report, mock_preview_report,
                               mock_list_preview, mock_list,
                               mock_get_bldg, mock_get_preview):
        """Test get_bes_buildings"""
        bes_ids = [1111]

        bldg = {'id': 1112, 'status_type_id': 1}
        preview_bldg = {'building_id': 1112}
        mock_preview_report.return_value = bldg, 'Rated'
        mock_get_preview.return_value = self.mock_building
        mock_get_bldg.return_value = self.mock_building
        mock_full_report.return_value = self.mock_building, 'Rated'

        list(get_bes_buildings(
            [], bes_ids=bes_ids, full_bldg=True,
            status_map=self.status_map, base_url=BASE_URL
        ))
        self.assertTrue(mock_get_bldg.called)
        self.assertTrue(mock_full_report.called)
        self.assertFalse(mock_list.called)

        mock_list.return_value = [self.mock_building]
        mock_list_preview.return_value = []

        list(get_bes_buildings(
            [], status_map=self.status_map, base_url=BASE_URL
        ))
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_list_preview.called)
        self.assertFalse(mock_preview_report.called)
        mock_list.return_value = [self.mock_building, bldg]
        mock_list_preview.return_value = [preview_bldg]
        mock_preview_report.return_value = bldg, 'Rated'
        list(get_bes_buildings(
            [], status_map=self.status_map, base_url=BASE_URL
        ))
        self.assertTrue(mock_preview_report.called)

        incomplete = []
        mock_preview_report.return_value = None, 'Editing'
        list(get_bes_buildings(
            incomplete, status_map=self.status_map, base_url=BASE_URL
        ))
        self.assertTrue(len(incomplete) > 0)
        self.assertEqual(incomplete[0].bldg_id, 1112)
