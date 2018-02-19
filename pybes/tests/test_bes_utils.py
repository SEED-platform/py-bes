#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved.
..codeauthor::Fable Turas <fable@raintechpdx.com>

Unit tests for pybes.utils.bes_utils functions
"""

# Imports from Standard Library
import sys
from unittest import TestCase

# Local Imports
from pybes.utils.bes_utils import convert_bes_year

PY3 = sys.version_info[0] == 3
if PY3:
    from unittest import mock
else:
    import mock
# Constants

# Helper Functions & Classes


# Tests
class BESUtilTests(TestCase):
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

    def test_convert_bes_year(self):
        """Test convert_bes_year"""
        value = 1899
        expected = 1900
        result = convert_bes_year(value)
        self.assertEqual(expected, result)

        values = [1900, 1901, '2017']

        for value in values:
            result = convert_bes_year(value)
            self.assertEqual(value, result)
