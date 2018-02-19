#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved
..codeauthor::Paul Munday <paul@paulmunday.net>

pybes tests
"""

# Imports from Standard Library
import random
import string
import sys
import unittest

# Imports from Third Party Modules
import requests

# Local Imports
import pybes.pybes as pybes
from pybes.pybes import TIMEOUT

PY3 = sys.version_info[0] == 3
if PY3:
    from unittest import mock
else:
    import mock

API_VERSION = '2'
BASE_URL = 'https://api.labworks.org/api'

# Constants
TEST_BUILDING = {
    u'address': u'12345 1st St',
    u'assessment_type': u'Test',
    u'blocks': [
        {
            u'block_id': 103,
            u'floor:floor_type': u'Slab-on-Grade',
            u'floor:floor_type_status!': u'Do not know',
            u'hvac_system:fuel_type': u'Natural Gas',
            u'hvac_system:fuel_type_status!': u'Do not know',
            u'hvac_system:type': u'Packaged Rooftop Air Conditioner',
            u'hvac_system:type_status!': u'Do not know',
            u'lighting':
                [
                    {
                        u'fixture_status!': u'Do not know',
                        u'id': 96,
                        u'lamp_type': u'Fluorescent T12',
                        u'mounting_type': u'Recessed',
                        u'percent_served': 80.0,
                        u'percent_served_status!': u'Do not know'},
                    {
                        u'fixture_status!': u'Do not know',
                        u'id': 97,
                        u'lamp_type': u'Incandescent/Halogen',
                        u'mounting_type': u'Recessed',
                        u'percent_served': 20.0,
                        u'percent_served_status!': u'Do not know'
                    }
                ],
            u'roof:roof_type': u'Built-up w/ metal deck',
            u'roof:roof_type_status!': u'Do not know',
            u'surfaces:window_wall_ratio': u'0.33',
            u'surfaces:window_wall_ratio_status!': u'Do not know',
            u'use_type:name!': u'Library',
            u'wall:wall_type': u'Brick/Stone on masonry',
            u'wall:wall_type_status!': u'Do not know',
            u'water_heater:fuel_type': u'Natural Gas',
            u'water_heater:fuel_type_status!': u'Do not know',
            u'window:framing_type': u'Metal w/ Thermal Breaks',
            u'window:framing_type_status!': u'Do not know',
            u'window:glass_type': u'Double Pane',
            u'window:glass_type_status!': u'Do not know'
        }
    ],
    u'building_id': 138,
    u'city': u'Boring',
    u'name': u'Test Building 1',
    u'notes': u'Built via V2 API',
    u'orientation!': u'North/South',
    u'state': u'Or',
    u'status!': u'Editing',
    u'total_floor_area!': 2000.0,
    u'year_of_construction': 1984,
    u'zip_code': u'97009'
}

# Helper Functions & Classes


# Tests
class MiscTests(unittest.TestCase):

    def test_fix_params(self):
        """Test _fix_params"""
        params = {1: True, 2: 'true', 3: False, 4: 'False'}
        expected = {1: True, 2: True, 3: 'False', 4: 'False'}
        result = pybes._fix_params(params)
        self.assertEqual(expected, result)

    def test_get_block_resource(self):
        """Test _get_block_resource"""
        expected = ('block_air_handlers', 'air_handler_id')

        result = pybes._get_block_resource('block_air_handlers')
        self.assertEqual(expected, result)

        result = pybes._get_block_resource('air_handler')
        self.assertEqual(expected, result)

        result = pybes._get_block_resource('air handler')
        self.assertEqual(expected, result)

        with self.assertRaises(pybes.BESError) as conm:
            pybes._get_block_resource('nope')
        error = conm.exception
        self.assertEqual(
            error.message, 'nope is not a valid block resource name'
        )

    def test_get_resource_name(self):
        """Test _get_resource_name"""
        expected = 'air_handlers'

        result = pybes._get_resource_name('air_handlers')
        self.assertEqual(expected, result)

        result = pybes._get_resource_name('air_handler')
        self.assertEqual(expected, result)

        result = pybes._get_resource_name('air handler')
        self.assertEqual(expected, result)

        with self.assertRaises(pybes.BESError) as conm:
            pybes._get_resource_name('nope')
        error = conm.exception
        self.assertEqual(
            error.message, 'nope is not a valid resource name'
        )

    def test_get_resource_type(self):
        """Test _get_resource_type"""
        expected = 'air_handler_types'

        result = pybes._get_resource_type('air_handlers')
        self.assertEqual(expected, result)

        result = pybes._get_resource_type('air_handler')
        self.assertEqual(expected, result)

        result = pybes._get_resource_type('air handler')
        self.assertEqual(expected, result)

        with self.assertRaises(pybes.BESError) as conm:
            pybes._get_resource_type('nope')
        error = conm.exception
        self.assertEqual(
            error.message, 'nope is not a valid resource type'
        )

    def test_params_from_dict(self):
        """Test _params from dict function."""
        test_dict = {
            'api_version': 'v2',
            'action': 'action',
            'kwargs': {'kwargs_a': 1},
            'id': 100,
            'self': 'self',
            'null_param': None,
            'empty_param': None,
            'param1': 'test',
            'param2': 2,
            'param3': False,
        }

        # test no exclude or required
        expected = {
            'param1': 'test',
            'param2': 2,
            'param3': False,
        }
        self.assertEqual(
            expected, pybes._params_from_dict(test_dict)
        )

        # test with exclude
        expected = {
            'param1': 'test',
            'param3': False,
        }
        result1 = pybes._params_from_dict(test_dict, exclude=['param2'])
        result2 = pybes._params_from_dict(test_dict, exclude='param2')
        self.assertEqual(expected, result1)
        self.assertEqual(expected, result2)

        # test_with_required
        with self.assertRaises(pybes.BESError) as conm:
            pybes._params_from_dict(test_dict, required='null_param')
        error = conm.exception
        self.assertEqual(
            error.message, 'The following keys can not be null: null_param'
        )

        with self.assertRaises(pybes.BESError) as conm:
            pybes._params_from_dict(
                test_dict, required=['null_param', 'empty_param']
            )
        error = conm.exception
        self.assertEqual(
            error.message,
            'The following keys can not be null: null_param, empty_param'
        )

    def test_split_key(self):
        """Test _split_key function."""
        # no subkey
        expected = ('key1', 1)
        result = pybes._split_key({}, 'key1', 1)
        self.assertEqual(expected, result)

        # subkey
        test_dict = {'subkey': 1}
        expected = ('key', test_dict)
        result = pybes._split_key({}, 'key:subkey', 1)
        self.assertEqual(expected, result)

        # returns dict with existing split
        test_dict = {'key': {'subkey1': 1}}
        expected = ('key', {'subkey1': 1, 'subkey2': 2})
        result = pybes._split_key(test_dict, 'key:subkey2', 2)
        self.assertEqual(expected, result)

        # won't raise  error
        test_dict = {'key': {'subkey0': 0, 'subkey1': 1}}
        expected = ('key', {'subkey0': 0, 'subkey1': 1, 'subkey2': 2})
        result = pybes._split_key(test_dict, 'key:subkey2', 2)
        self.assertEqual(expected, result)

        # raises error if subkey present
        test_dict = {'key': {'subkey1': 1, 'subkey2': 2}}
        with self.assertRaises(pybes.BESError) as conm:
            pybes._split_key(test_dict, 'key:subkey2', 3)
        error = conm.exception
        expected = 'Subkey subkey2 already exists in dct[key]'
        self.assertEqual(expected, error.message)

    def test_verify_password(self):
        """Test _verify_password function."""
        uppercase = random.sample(string.ascii_uppercase, 2)
        lowercase = random.sample(string.ascii_lowercase, 2)
        digits = random.sample(string.digits, 2)
        symbols = random.sample(string.punctuation, 2)
        # must contain symbol
        self.assertRaises(
            pybes.BESError, pybes._verify_password,
            "".join(uppercase + lowercase + digits), min_chars=6
        )
        # must contain digit
        self.assertRaises(
            pybes.BESError, pybes._verify_password,
            "".join(uppercase + lowercase + symbols), min_chars=6
        )
        # must contain  lowercase letter
        self.assertRaises(
            pybes.BESError, pybes._verify_password,
            "".join(uppercase + symbols + digits), min_chars=6
        )
        # must contain  uppercase letter
        self.assertRaises(
            pybes.BESError, pybes._verify_password,
            "".join(lowercase + digits + symbols), min_chars=6
        )
        good_password = "".join(uppercase + lowercase + digits + symbols)
        # must be at least min_chars long
        self.assertRaises(
            pybes.BESError, pybes._verify_password,
            good_password, min_chars=len(good_password) + 1
        )
        # contains uppper case, lowercase, digit and symbol and is 8 + chars
        self.assertEqual(pybes._verify_password(good_password), good_password)
        # test with 1 of each + padding
        good_password = "".join(
            [char for idx, char in enumerate(good_password) if idx % 2 == 0]
        ) + 'xxxx'
        self.assertEqual(pybes._verify_password(good_password), good_password)

    def test_unroll(self):
        """Test function for unrolling results"""
        unrolled = pybes.unroll(TEST_BUILDING)
        self.assertIn('floor', unrolled['blocks'][0].keys())
        self.assertEqual(
            unrolled['blocks'][0]['floor'],
            {
                u'floor_type': u'Slab-on-Grade',
                u'floor_type_status!': u'Do not know'
            }
        )

    def test_remove_unknown(self):
        """Test function for removing unknown results"""
        unrolled = pybes.unroll(TEST_BUILDING)
        result = pybes.remove_unknown(unrolled)
        self.assertNotIn('floor', result['blocks'][0].keys())

    def test_exception(self):
        """Test BESError"""
        error = pybes.BESError('test', code=1)
        self.assertEqual(1, error.code)
        self.assertEqual('test', error.message)
        self.assertEqual('test', str(error))
        self.assertEqual('<BESError: "test">', repr(error))


@mock.patch('pybes.pybes.requests')
class TestAPIGenerics(unittest.TestCase):
    """Test generic api client functionality"""

    def setUp(self):
        self.endpoint = 'endpoint'
        self.token = 'token'
        self.url = "{}/v{}/{}".format(BASE_URL, API_VERSION, self.endpoint)
        self.client = pybes.BESClient(
            access_token=self.token, base_url=BASE_URL
        )

    def test_authenticate(self, mock_requests):
        """test _authenticate method (via init)."""
        params = {
            'email': 'test@test.org',
            'password': 'password',
            'organization_token': 'org_token',
            'base_url': BASE_URL
        }

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = True
        mock_response.json.return_value = {
            'user_id': 1, 'token': self.token
        }

        mock_requests.post.return_value = mock_response

        client = pybes.BESClient(**params)

        url = "{}/v{}/{}".format(
            BASE_URL, API_VERSION, 'users/authenticate'
        )
        request_params = params.copy()
        request_params.pop('base_url')
        request_params['password_confirmation'] = params['password']

        mock_requests.post.assert_called_with(
            url, timeout=client.timeout, json=request_params
        )

        self.assertEqual(client.token, self.token)
        self.assertEqual(client.user_id, 1)

    def test_get(self, mock_requests):
        """Test _get method"""
        mock_response = mock.MagicMock()
        mock_requests.get.return_value = mock_response
        expected = {
            'timeout': TIMEOUT,
            'params': {'token': self.token, 'a': 1}
        }

        result = self.client._get(self.endpoint, a=1)
        mock_requests.get.assert_called_with(self.url, **expected)
        self.assertEqual(mock_response, result)

    def test_post(self, mock_requests):
        """Test _post method"""
        mock_response = mock.MagicMock()
        mock_requests.post.return_value = mock_response
        expected = {
            'timeout': TIMEOUT,
            'files': 'files',
            'json': {'token': self.token, 'a': 1}
        }

        result = self.client._post(self.endpoint, files='files', a=1)
        mock_requests.post.assert_called_with(self.url, **expected)
        self.assertEqual(mock_response, result)

    def test_put(self, mock_requests):
        """Test _put method"""
        mock_response = mock.MagicMock()
        mock_requests.put.return_value = mock_response

        expected = {
            'timeout': TIMEOUT,
            'files': 'files',
            'json': {'token': self.token, 'a': 1}
        }
        result = self.client._put(self.endpoint, files='files', a=1)
        mock_requests.put.assert_called_with(self.url, **expected)
        self.assertEqual(mock_response, result)

        expected = {
            'timeout': TIMEOUT,
            'params': {'token': self.token, 'a': 1}
        }
        self.client._put(self.endpoint, use_json=False, a=1)
        mock_requests.put.assert_called_with(self.url, **expected)

    def test_patch(self, mock_requests):
        """Test _patch method"""
        mock_response = mock.MagicMock()
        mock_requests.patch.return_value = mock_response
        expected = {
            'timeout': TIMEOUT,
            'files': 'files',
            'json': {'token': self.token, 'a': 1}
        }

        result = self.client._patch(self.endpoint, files='files', a=1)
        mock_requests.patch.assert_called_with(self.url, **expected)
        self.assertEqual(mock_response, result)

    def test_delete(self, mock_requests):
        """Test _delete method"""
        mock_response = mock.MagicMock()
        mock_requests.delete.return_value = mock_response
        expected = {
            'timeout': TIMEOUT,
            'params': {'token': self.token}
        }
        url = self.url + '/1'

        result = self.client._delete(self.endpoint, id=1)
        mock_requests.delete.assert_called_with(url, **expected)
        self.assertEqual(mock_response, result)


class TestAPIGenericsNoCall(unittest.TestCase):
    """Test generic api client functionality that doesn't hit api"""

    def setUp(self):
        self.client = pybes.BESClient(base_url=BASE_URL)

    def test_check_call_success(self):
        """Test _check_call_success method"""
        mock_response = mock.MagicMock()

        # test no error
        self.client._check_call_success(mock_response)
        assert True     # not reached if error raised

        # test errors
        mock_response.status_code = 404

        mock_response.raise_for_status.side_effect = requests.HTTPError()

        # test json error messages
        # single error
        mock_response.json.return_value = {'error': 'test'}
        with self.assertRaises(pybes.APIError) as conm:
            self.client._check_call_success(mock_response, prefix='Test')
        error = conm.exception
        self.assertEqual(error.message, 'Test: 404 test')

        # multiple errors
        mock_response.json.return_value = {
            'errors': {'test': 'error', 'error': 'test'}
        }
        with self.assertRaises(pybes.APIError) as conm:
            self.client._check_call_success(mock_response, prefix='Test')
        error = conm.exception
        assert (
            error.message == 'Test: 404 test: error, error: test' or
            error.message == 'Test: 404 error: test, test: error'
        )

        # error as string
        mock_response.json.side_effect = ValueError()
        mock_response.content = 'error content'
        with self.assertRaises(pybes.APIError) as conm:
            self.client._check_call_success(mock_response, prefix='Test')
        error = conm.exception
        self.assertEqual(error.message, 'Test: 404 error content')

        # test default/error as html
        mock_response.content = '<!DOCTYPE html>'
        with self.assertRaises(pybes.APIError) as conm:
            self.client._check_call_success(mock_response, default='default')
        error = conm.exception
        self.assertEqual(error.message, '404 default')

        # v1 style errors
        mock_response.content = 'v1 error\nother stuff'
        with self.assertRaises(pybes.APIError) as conm:
            self.client._check_call_success(
                mock_response, prefix='Test', default='foo'
            )
        error = conm.exception
        self.assertEqual(error.message, 'Test: 404 v1 error')

    def test_construct_payload(self):
        """Test _construct_payload method"""
        # doesn't add token if not set on self
        expected = {'key': 'val'}
        result = self.client._construct_payload({'key': 'val'})
        self.assertEqual(expected, result)

        # adds token if set on self
        self.client.token = 'token'
        expected = {'key': 'val', 'token': 'token'}
        result = self.client._construct_payload({'key': 'val'})
        self.assertEqual(expected, result)

    def test_construct_url(self):
        """Test _construct_url method"""
        first = "{}/v{}/".format(BASE_URL, API_VERSION)
        endpoint = 'endpoint'

        expected = first + endpoint
        result = self.client._construct_url(endpoint)
        self.assertEqual(expected, result)
        # strips '/' from endpoint
        result = self.client._construct_url('/endpoint/')
        self.assertEqual(expected, result)

        expected = "{}{}/{}".format(first, endpoint, '1')
        result = self.client._construct_url(endpoint, id=1)
        self.assertEqual(expected, result)

        expected = "{}{}/{}/action".format(first, endpoint, 1)
        result = self.client._construct_url(endpoint, id=1, action='action')
        self.assertEqual(expected, result)
        # strips '/' from  action
        result = self.client._construct_url(
            endpoint, id=1, action='/action'
        )
        self.assertEqual(expected, result)

        expected = 'baseurl/v2/endpoint'
        result = self.client._construct_url(endpoint, base_url='baseurl')
        self.assertEqual(expected, result)

        expected = BASE_URL + '/v1/endpoint'
        result = self.client._construct_url(
            endpoint, api_version='v1'
        )
        self.assertEqual(expected, result)

        # converts api_id if int (and id if string)
        expected = BASE_URL + '/v1/endpoint/2/action'
        result = self.client._construct_url(
            endpoint, api_version=1, id='2', action='action'
        )
        self.assertEqual(expected, result)

        # raises errror if action and no id
        with self.assertRaises(pybes.BESError) as conm:
            self.client._construct_url(endpoint, action='action')
        error = conm.exception
        self.assertEqual(
            error.message, 'id must be supplied with action'
        )


@mock.patch('pybes.pybes.requests')
class TestPreviewBuildingAPI(unittest.TestCase):
    """Test public api client functionality for Preview Buildings."""

    def setUp(self):
        self.id = 1
        self.mock_response = mock.MagicMock()
        self.json = {'json': 'test'}
        self.mock_response.json.return_value = self.json
        self.mock_response.content = 'pdf'
        self.mock_response.raise_for_status.return_value = True
        self.token = 'token'
        self.client = pybes.BESClient(
            access_token=self.token, base_url=BASE_URL
        )
        self.url = self.client._construct_url('preview_buildings')
        self.id_url = "{}/{}".format(self.url, self.id)

    def test_create_preview_building(self, mock_requests):
        """Test create_preview_building call."""
        building = {
            'assessment_type': 'Test',
            'building_name': 'test building',
            'year_completed': '1984',
            'floor_area': '2000',
            'street': '123 Nowhere St',
            'city': 'Boring',
            'state': 'OR',
            'postal_code': '97009',
            'use_type': 'Library',
            'orientation': 'North/South',
            'number_floors': '100'
        }

        mock_requests.post.return_value = self.mock_response
        expected = {
            'building': building,
            'token': self.token
        }
        self.client.create_preview_building(**building)
        mock_requests.post.assert_called_with(
            self.url, json=expected, timeout=TIMEOUT
        )

    def test_delete_preview_building(self, mock_requests):
        """Test delete_preview_building call."""
        self.client.delete_preview_building(self.id)
        mock_requests.delete.assert_called_with(
            self.id_url, params={'token': self.token}, timeout=TIMEOUT
        )

    def test_duplicate_preview_building(self, mock_requests):
        """Test duplicate_preview_building call."""
        self.client.duplicate_preview_building(self.id)
        url = self.id_url + '/duplicate'
        mock_requests.get.assert_called_with(
            url, params={'token': self.token}, timeout=TIMEOUT
        )

    def test_get_preview_building(self, mock_requests):
        """Test get_preview_building call."""
        mock_requests.get.return_value = self.mock_response

        # without report type
        result = self.client.get_preview_building(self.id)
        mock_requests.get.assert_called_with(
            self.id_url, params={'token': self.token}, timeout=TIMEOUT
        )
        self.assertEqual(self.json, result)

        # simple report
        result = self.client.get_preview_building(
            self.id, report_type='simple'
        )
        url = self.id_url + '/simple'
        mock_requests.get.assert_called_with(
            url, params={'token': self.token}, timeout=TIMEOUT
        )
        self.assertEqual(self.json, result)

        # pdf report
        result = self.client.get_preview_building(
            self.id, report_type='pdf'
        )
        url = self.id_url + '/report'
        mock_requests.get.assert_called_with(
            url, params={'token': self.token}, timeout=TIMEOUT
        )
        self.assertEqual(self.json, result)

        # check error reporting
        self.assertRaises(
            pybes.BESError, self.client.get_preview_building, 1,
            report_type='wrong'
        )

    def test_list_preview_buildings(self, mock_requests):
        """Test list_preview_building call."""
        self.client.list_preview_buildings()
        mock_requests.get.assert_called_with(
            self.url, params={'token': self.token}, timeout=TIMEOUT
        )

    def test_simulate_preview_building(self, mock_requests):
        """Test simulate_preview_building call."""
        self.client.simulate_preview_building(self.id)
        url = self.id_url + '/simulate'
        mock_requests.get.assert_called_with(
            url, params={'token': self.token}, timeout=TIMEOUT
        )

    def test_update_preview_building(self, mock_requests):
        """Test update_preview_building call."""
        building = {
            'assessment_type': 'Test',
            'name': 'test building',
            'year_of_construction': '1984',
            'address': '123 Nowhere St',
            'city': 'Boring',
            'state': 'OR',
            'zip_code': '97009',
            'notes': 'test'
        }
        block_id = 2

        mock_requests.put.return_value = self.mock_response
        expected_building = building.copy()
        expected_building['block_id'] = block_id
        expected = {
            'building': expected_building,
            'token': self.token
        }
        self.client.update_preview_building(self.id, block_id, **building)
        mock_requests.put.assert_called_with(
            self.id_url, json=expected, timeout=TIMEOUT
        )

    def test_validate_preview_building(self, mock_requests):
        """Test validate_preview_building call."""
        self.client.validate_preview_building(self.id)
        url = self.id_url + '/validate'
        mock_requests.get.assert_called_with(
            url, params={'token': self.token}, timeout=TIMEOUT
        )


@mock.patch('pybes.pybes.requests')
class TestHESUserAPI(unittest.TestCase):
    """Test public api client functionality for User Management."""

    def setUp(self):
        self.id = 1
        self.org_id = 2
        self.role_id = 3
        self.email = 'test@example.org'
        self.password = 'Ssh!1ts@secret'
        self.first = 'first'
        self.last = 'last'
        self.mock_response = mock.MagicMock()
        self.json = {
            'id': self.id, 'organization_id': self.org_id,
            'role_id': self.role_id
        }
        self.mock_response.json.return_value = self.json
        self.mock_response.raise_for_status.return_value = True
        self.token = 'token'
        self.client = pybes.BESClient(
            access_token=self.token, base_url=BASE_URL
        )
        self.url = self.client._construct_url('users')
        self.id_url = "{}/{}".format(self.url, self.id)

    def test_get_user(self, mock_requests):
        """Test get_user method"""
        mock_requests.get.return_value = self.mock_response
        result = self.client.get_user(self.id)
        mock_requests.get.assert_called_with(
            self.id_url, params={'token': self.token}, timeout=TIMEOUT
        )
        self.assertEqual(self.json, result)

    def test_update_user(self, mock_requests):
        """Test update_user method"""
        mock_requests.put.return_value = self.mock_response
        params = {
            'email': self.email,
            'password': self.password,
            'password_confirmation': self.password,
            'first_name': self.first,
            'last_name': self.last,

        }
        expected = params.copy()
        expected['token'] = self.token
        result = self.client.update_user(self.id, **params)
        mock_requests.put.assert_called_with(
            self.id_url, json=expected, timeout=TIMEOUT
        )
        self.assertIsNone(result)

        # test errors
        params['password_confirmation'] = None
        with self.assertRaises(pybes.BESError) as conm:
            self.client.update_user(self.id, **params)
        error = conm.exception
        expected = "Password and password_confirmation must be supplied"
        self.assertEqual(expected, error.message)

        params['password_confirmation'] = 'Nope'
        with self.assertRaises(pybes.BESError) as conm:
            self.client.update_user(self.id, **params)
        error = conm.exception
        expected = "Passwords do not match!"
        self.assertEqual(expected, error.message)

    def test_create_api_user(self, mock_requests):
        """Test create_api_user function"""
        mock_requests.post.return_value = self.mock_response
        expected = {
            'organization_token': 'orgtoken',
            'email': self.email,
            'password': self.password,
            'password_confirmation': self.password,
            'first_name': self.first,
            'last_name': self.last,
        }
        result = pybes.create_api_user(
            'orgtoken', self.email, self.password, self.password,
            self.first, self.last, BASE_URL
        )
        mock_requests.post.assert_called_with(
            self.url, json=expected, timeout=TIMEOUT
        )
        self.assertEqual((self.id, self.org_id, self.role_id), result)

        # test error
        with self.assertRaises(pybes.BESError) as conm:
            pybes.create_api_user(
                'orgtoken', self.email, self.password, 'Nope!',
                self.first, self.last, BASE_URL
            )
        error = conm.exception
        expected = "Passwords do not match!"
        self.assertEqual(expected, error.message)


@mock.patch('pybes.pybes.requests')
class TestBlockAPI(unittest.TestCase):
    """Test public api client functionality for Blocks."""

    def setUp(self):
        self.id = 1
        self.mock_response = mock.MagicMock()
        self.json = {'json': 'test'}
        self.mock_response.json.return_value = self.json
        self.mock_response.raise_for_status.return_value = True
        self.token = 'token'
        self.client = pybes.BESClient(
            access_token=self.token, base_url=BASE_URL
        )
        self.url = self.client._construct_url('blocks', api_version=1)
        self.id_url = "{}/{}".format(self.url, self.id)

    def test_create_block(self, mock_requests):
        """Test create_block method"""
        mock_requests.post.return_value = self.mock_response
        url = self.client._construct_url(
            'buildings', id=1, action='blocks', api_version=1
        )
        expected = {
            'name': 'test',
            'shape_id': 2,
            'floor_to_floor_height': 9,
            'floor_to_ceiling_height': 8,
            'is_above_ground': True,
            'number_of_floors': 3,
            'orientation': 10,
            'position': '1,1',
            'vertices': '1,1',
            'dimension_1': 100,
            'dimension_2': 100,
            'has_drop_ceiling': "False",
            'token': self.token,
        }
        result = self.client.create_block(
            1, 2, 'test', 9, 8, True, 3, 10, '1,1', '1,1', 100, 100,
            has_drop_ceiling=False
        )
        mock_requests.post.assert_called_with(
            url, json=expected, timeout=TIMEOUT
        )
        self.assertEqual(result, self.json)

    def test_delete_block(self, mock_requests):
        """Test delete_block method"""
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        self.client.delete_block(self.id)
        mock_requests.delete.assert_called_with(self.id_url, **expected)

    def test_get_block(self, mock_requests):
        """Test get_block method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_block(self.id)
        mock_requests.get.assert_called_with(self.id_url, **expected)
        self.assertEqual(result, self.json)

    def test_update_block(self, mock_requests):
        """Test update_block method"""
        expected = {
            'json': {'token': 'token', 'shape_id': 2, 'name': 'test'},
            'timeout': TIMEOUT
        }
        self.client.update_block(self.id, 2, name='test')
        mock_requests.put.assert_called_with(self.id_url, **expected)

    def test_create_block_resource(self, mock_requests):
        """Test create_block_resource method"""
        mock_requests.post.return_value = self.mock_response
        url = self.client._construct_url(
            'blocks', id=1, action='block_air_handlers', api_version=1
        )
        params = {
            'air_handler_id': 2,
            'token': self.token,
        }
        name = 'test'
        result = self.client.create_block_resource(
            'air handler', 1, name, **params
        )
        params.update({'name': name})
        mock_requests.post.assert_called_with(
            url, json=params, timeout=TIMEOUT
        )
        self.assertEqual(result, self.json)

    def test_delete_block_resource(self, mock_requests):
        """Test delete_block_resource method"""
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        self.client.delete_block_resource('air_handler', self.id)
        mock_requests.delete.assert_called_with(
            self.id_url.replace('blocks', 'block_air_handlers'), **expected
        )

    def test_get_block_resource(self, mock_requests):
        """Test get_block_resource method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_block_resource('air_handler', self.id)
        mock_requests.get.assert_called_with(
            self.id_url.replace('blocks', 'block_air_handlers'), **expected
        )
        self.assertEqual(result, self.json)

    def test_get_block_resources(self, mock_requests):
        """Test get_block_resources method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_block_resources('air_handler', self.id)
        mock_requests.get.assert_called_with(
            self.id_url + '/block_air_handlers', **expected
        )
        self.assertEqual(result, self.json)

    def test_update_block_resource(self, mock_requests):
        """Test update_block_resource method"""
        expected = {
            'json': {'token': 'token', 'air_handler_id': 2, 'name': 'test'},
            'timeout': TIMEOUT
        }
        self.client.update_block_resource(
            'air_handler', self.id, 2, name='test'
        )
        mock_requests.put.assert_called_with(
            self.id_url.replace('blocks', 'block_air_handlers'), **expected
        )


@mock.patch('pybes.pybes.requests')
class TestBuildingAPI(unittest.TestCase):
    """Test public api client functionality for Buildings."""

    def setUp(self):
        self.id = 1
        self.mock_response = mock.MagicMock()
        self.json = {'json': 'test'}
        self.mock_response.content = 'test content'
        self.mock_response.json.return_value = self.json
        self.mock_response.raise_for_status.return_value = True
        self.token = 'token'
        self.client = pybes.BESClient(
            access_token=self.token, base_url=BASE_URL
        )
        self.url = self.client._construct_url('buildings', api_version=1)
        self.id_url = "{}/{}".format(self.url, self.id)

    def test_create_building(self, mock_requests):
        """Test create_building method"""
        mock_requests.post.return_value = self.mock_response
        expected = {
            'name': 'test',
            'assessment_type_id': 1,
            'year_of_construction': '1984',
            'address': '1234 1st St',
            'city': 'Boring',
            'state': 'OR',
            'zip_code': 97009,
            'reported_floor_area': 100,
            'notes': 'test',
            'token': self.token,
        }
        result = self.client.create_building(
            1, 'test', '1984', '1234 1st St', 'Boring', 'OR', 97009, 100,
            notes='test'
        )
        mock_requests.post.assert_called_with(
            self.url, json=expected, timeout=TIMEOUT
        )
        self.assertEqual(result, self.json)

    def test_get_building(self, mock_requests):
        """Test get_building method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_building(self.id)
        mock_requests.get.assert_called_with(self.id_url, **expected)
        self.assertEqual(result, self.json)

        result = self.client.get_building(self.id, report_type='pdf')
        mock_requests.get.assert_called_with(
            self.id_url + '/report', **expected
        )
        self.assertEqual(result, self.mock_response.content)
        self.assertRaises(
            pybes.BESError, self.client.get_building,
            self.id, report_type='wrong'
        )

    def test_get_building_blocks(self, mock_requests):
        """Test get_building_blocks method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_building_blocks(self.id)
        mock_requests.get.assert_called_with(
            self.id_url + '/blocks', **expected
        )
        self.assertEqual(result, self.json)

    def test_get_building_resources(self, mock_requests):
        """Test get_building_resources method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_building_resources('air_handler', self.id)
        mock_requests.get.assert_called_with(
            self.id_url + '/air_handlers', **expected
        )
        self.assertEqual(result, self.json)

    def test_get_building_score(self, mock_requests):
        """Test get_building_score method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_building_score(self.id)
        mock_requests.get.assert_called_with(
            self.id_url + '/score', **expected
        )
        self.assertEqual(result, self.json)

    def test_list_buildings(self, mock_requests):
        """Test list_buildings method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.list_buildings()
        mock_requests.get.assert_called_with(self.url, **expected)
        self.assertEqual(result, self.json)

    def test_manage_buildings(self, mock_requests):
        """Test manage_buildings method"""
        url = self.client._construct_url(
            'manage_buildings', action='csv', api_version=1, noid=True
        )
        expected = {
            'params': {'token': 'token', 'building_ids': '1,2,3'},
            'timeout': TIMEOUT
        }
        self.client.manage_buildings(1, 2, 3)
        mock_requests.get.assert_called_with(url, **expected)

    def test_simulate_building(self, mock_requests):
        """Test simulate_building method"""
        mock_requests.post.return_value = self.mock_response
        expected = {'json': {'token': 'token'}, 'timeout': TIMEOUT}
        self.client.simulate_building(self.id)
        mock_requests.post.assert_called_with(
            self.id_url + '/simulate', **expected
        )

    def test_update_building(self, mock_requests):
        """Test update_building method"""
        expected = {
            'json': {'token': 'token', 'notes': 'test'},
            'timeout': TIMEOUT
        }
        self.client.update_building(self.id, notes='test')
        mock_requests.put.assert_called_with(self.id_url, **expected)

    def test_validate_building(self, mock_requests):
        """Test validate_building method"""
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {'valid': True}
        mock_response.raise_for_status.return_value = True
        mock_requests.get.return_value = mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.validate_building(self.id)
        mock_requests.get.assert_called_with(
            self.id_url + '/validate', **expected
        )
        self.assertTrue(result)

        # test invalid
        mock_response.json.return_value = {
            'valid': False, 'errors': ['error1', 'error2']
        }
        expected = 'Unable to validate building 1: error1, error2'
        with self.assertRaises(pybes.APIError) as conm:
            self.client.validate_building(self.id)
        error = conm.exception
        self.assertEqual(expected, error.message)

    def test_create_resource(self, mock_requests):
        """Test create_resource method"""
        mock_requests.post.return_value = self.mock_response
        url = self.client._construct_url(
            'buildings', id=1, action='air_handlers', api_version=1
        )
        expected = {
            'name': 'test',
            'token': self.token,
        }
        result = self.client.create_resource(
            'air handler', 1, name='test'
        )
        mock_requests.post.assert_called_with(
            url, json=expected, timeout=TIMEOUT
        )
        self.assertEqual(result, self.json)

    def test_delete_resource(self, mock_requests):
        """Test delete_resource method"""
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        self.client.delete_resource('air_handler', self.id)
        mock_requests.delete.assert_called_with(
            self.id_url.replace('buildings', 'air_handlers'),
            **expected
        )

    def test_get_resource(self, mock_requests):
        """Test get_resource method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_resource('air_handler', self.id)
        mock_requests.get.assert_called_with(
            self.id_url.replace('buildings', 'air_handlers'),
            **expected
        )
        self.assertEqual(result, self.json)

    def test_update_resource(self, mock_requests):
        """Test update_resource method"""
        expected = {
            'json': {'token': 'token', 'name': 'test'},
            'timeout': TIMEOUT
        }
        self.client.update_resource(
            'air_handler', self.id, name='test'
        )
        mock_requests.put.assert_called_with(
            self.id_url.replace('buildings', 'air_handlers'),
            **expected
        )

    def test_get_resource_type(self, mock_requests):
        """Test get_resource_type method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.get_resource_type('air_handler', self.id)
        mock_requests.get.assert_called_with(
            self.id_url.replace('buildings', 'air_handler_types'),
            **expected
        )
        self.assertEqual(result, self.json)

    def test_list_resource_type(self, mock_requests):
        """Test list_resource method"""
        mock_requests.get.return_value = self.mock_response
        expected = {'params': {'token': 'token'}, 'timeout': TIMEOUT}
        result = self.client.list_resource_types('air_handler')
        mock_requests.get.assert_called_with(
            self.url.replace('buildings', 'air_handler_types'),
            **expected
        )
        self.assertEqual(result, self.json)
