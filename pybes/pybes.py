#!/usr/bin/env python
"""
copyright (c) 2016 Earth Advantage. All rights reserved.
..codeauthor::Paul Munday <paul@paulmunday.net>

BES API Client"""


# Imports from Standard Library
from collections import (Mapping, Sequence)
import string
import sys

# Imports from External Modules
import requests

# Config/Constants
PY3 = sys.version_info[0] == 3
if PY3:
    basestring = str


UPPERCASE = set(string.ascii_uppercase)
LOWERCASE = set(string.ascii_lowercase)
DIGITS = set(string.digits)
SYMBOLS = set(string.punctuation)


# http://docs.python-requests.org/en/master/user/quickstart/#timeouts
TIMEOUT = 10

BLOCK_RESOURCES = {
    'air_handler': 'block_air_handlers',
    'fixture': 'block_fixtures',
    'surface': 'surfaces',
    'water_heater': 'block_water_heaters',
    'zone_equipment': 'block_zone_equipments',
}

BES_RESOURCES = [
    'air_handlers',
    'building_use_types',
    'fixtures',
    'floors',
    'operations',
    'plants',
    'roofs',
    'skylights',
    'surfaces',
    'walls',
    'water_heaters',
    'windows',
    'zone_equipments',
]

BES_RESOURCE_TYPES = {
    'air_handler': 'air_handler_types',
    'boiler': 'boiler_types',
    'chiller_pump_control': 'chiller_pump_control_types',
    'compressor': 'compressor_types',
    'condenser_pump_control': 'condenser_pump_control_types',
    'condenser': 'condenser_types',
    # 'condenser_loop': 'condenser_loop_types',
    'condenser_pump_control': 'condenser_pump_control_types',
    'cooling_tower_fan_control': 'cooling_tower_fan_control_types',
    'distribution': 'distribution_types',
    'fan_control': 'fan_controls',
    'floor': 'floor_types',
    'framing': 'framing_types',
    'fuel': 'fuel_types',
    'gas_fill': 'gas_fill_types',
    'glass': 'glass_types',
    'lamp': 'lamp_types',
    'mounting': 'mounting_types',
    'operating_season': 'operating_seasons',
    'plant': 'plant_types',
    'roof': 'roof_types',
    'shading': 'shading_types',
    'shape': 'shapes',
    'sink_source': 'sink_source_types',
    'skylight_layout': 'skylight_layouts',
    'skylight': 'skylight_types',
    'slab_insulation': 'slab_insulation_types',
    'status': 'status_types',
    'terminal_unit': 'terminal_units',
    'use': 'use_types',
    'use_type': 'use_types',
    'wall': 'wall_types',
    'window_layout': 'window_layouts',
    'zone_equipment': 'zone_equipment_types',
    'zone_layout': 'zone_layouts'
}


# Private Functions and Classes
def _fix_params(params):
    """For v1 api  -- True is True but False is a string"""
    for key, val in params.items():
        if val is False or str(val).lower() == 'false':
            params[key] = 'False'
        elif str(val).lower() == 'true':
            params[key] = True
    return params


def _get_block_resource(block_resource):
    """Perform conversions and check is valid"""
    blockres = block_resource.lower().rstrip('s').replace(
        ' ', '_'
    ).replace('block_', '')
    if blockres not in BLOCK_RESOURCES.keys():
        msg = "{} is not a valid block resource name".format(block_resource)
        raise BESError(msg)
    return BLOCK_RESOURCES[blockres], "{}_id".format(blockres)


def _get_resource_name(resource_name):
    """Perform conversions and check is valid"""
    rname = resource_name.lower().replace(' ', '_')
    if not rname.endswith('s'):
        rname = rname + 's'
    if rname not in BES_RESOURCES:
        msg = "{} is not a valid resource name".format(resource_name)
        raise BESError(msg)
    return rname


def _get_resource_type(resource_type):
    """Perform conversions and check is valid"""
    rtype = resource_type.lower().replace('_types', '').replace(' ', '_')
    if rtype not in ['glass', 'status']:
        rtype = rtype.rstrip('s')
    if rtype not in BES_RESOURCE_TYPES.keys():
        msg = "{} is not a valid resource type".format(resource_type)
        raise BESError(msg)
    return BES_RESOURCE_TYPES[rtype]


def _params_from_dict(dct, exclude=None, required=None):
    """
    Build dict of non null values, excluding keys in exclude (and self etc).
    kwargs is excluded as a key.
    required lists keys that can not be null.
    """
    if not exclude:
        exclude = []
    elif isinstance(exclude, basestring):
        exclude = [exclude]
    exclude.extend(
        ['self', 'kwargs', 'api_version', 'action', 'id', 'endpoint']
    )
    if required:
        if isinstance(required, basestring):
            required = [required]
        null = [
            key for key in required if not dct.get(key) and key not in exclude
        ]
        if null:
            msg = "The following keys can not be null: {}".format(
                ", ".join(null)
            )
            raise BESError(msg)
    return {
        key: val for key, val in dct.items()
        if val is not None and key not in exclude
    }


def _split_key(dct, key, val):
    """
    Used by unroll to transform {'key:subkey': val} -> {'key':{'subkey': val}}

    ..note: This does not mutate dct, only returns (new) key and value.
    To use this to transform all keys in a dict you can mutate in place::

        for key in my_dict.keys():
            val = my_dict.pop(key)      # remove it from the dict
            key, val = _split_key(my_dict, key, val)
            my_dict[key] = val          # add back

    or create a new dict and give this to _split keys, leaving the old intact::

        result = {}
        for key, val in my_dict.iteritems():
                key, val = _split_key(result, key, val)
                result[key] = val          # add key to result

    This is why you need to supply key, value and the dict. In the case of
    valuethere is is no assumption that it is in the supplied dict.
    Note,  however, there is an implict assumption that the supplied dict
    is mutated between calls:
    it is examined to see if a key matching the split has already been
    added to the dict, if so the sub key is added to existing sub dict. This
    allows you to assign the new value to the (new) key, straight away,
    without tracking whether it will overwrite anything. Its not required
    that this be the case, but if not you will need to track instances where
    a key has been split (by checking to see if key has changed).

    An error will be raised if a sub key already exists, in order to prevent
    it being accidently overwritten.
    """
    try:
        key, subkey = key.split(':', 1)
        subdict = dct.get(key, {}).copy()
        if subkey in subdict:
            msg = "Subkey {} already exists in dct[{}]".format(subkey, key)
            raise BESError(msg)
        subdict[subkey] = val
        val = subdict
    except ValueError:
        pass
    return key, val


def _verify_password(passwd, min_chars=8):
    """
    Matches BES password constraints and min length.
    Contains uppercase, lowercase, digit and special character.
    """
    pwd = set(passwd)
    # contains at least one char from each set
    contains_all_required = True if (
        pwd.intersection(UPPERCASE) and pwd.intersection(LOWERCASE)
        and pwd.intersection(DIGITS) and pwd.intersection(SYMBOLS)
    ) else False
    if not contains_all_required or len(passwd) < min_chars:
        msg = (
            "Passwords must be at least 8 characters long and contain an "
            "uppercase, lowercase, number and symbol character"
        )
        raise BESError(msg)
    return passwd


# Public Functions and Classes
def create_api_user(organization_token, email, password, password_confirmation,
                    first_name, last_name, base_url):
    # type(str, str, str, str, str, str) -> int, int, int
    """
    Create a new API user account.

    :param email: user's email
    :type email: str
    :param password: user's password
    :type password: str
    :param password_confirmation: user password  (repeated)
    :type password_confirmation: str
    :param first_name: user's first name
    :type first_name: str
    :param last_name: user's last name
    :type last_name: str
    :param organization_token: organization token
    :type organization_token: str

    :returns: int, int, int -- id, organization_id, role_id
    :raises: BESError/APIError
    """
    endpoint = 'users'
    if password != password_confirmation:
        msg = 'Passwords do not match!'
        raise BESError(msg)
    client = BESClient(base_url=base_url)
    password = _verify_password(password)
    params = {
        'organization_token': organization_token,
        'email': email,
        'password': password,
        'password_confirmation': password_confirmation,
        'first_name': first_name,
        'last_name': last_name
    }
    response = client._post(
        endpoint, compulsory_params=params.keys(), **params
    )
    client._check_call_success(response, prefix="Unable to create user.")
    user_id = response.json()['id']
    org_id = response.json()['organization_id']
    role_id = response.json()['role_id']
    return user_id, org_id, role_id


def get_resource_types(client):
    # type(BESClient) -> dict
    """Returns a lookup table for identyfiying resource type ids"""
    resource_types = {}
    for val in BES_RESOURCE_TYPES.values():
        try:
            resources = client.list_resource_types(val)
            resource_types[val] = {
                plt['display_name'].lower(): plt for plt in resources
            }
        except KeyError as err:
            resource_types[val] = {
                plt['name'].lower(): plt for plt in resources
            }
        except APIError as err:
            print(val, err.status_code, err.message)
    return resource_types


def remove_unknown(params):
    """
    Remove key & values from params if corresponding status is 'Do not know'.
    """
    if isinstance(params, Sequence) and not isinstance(params, basestring):
        result = []
        for item in params:
            res = remove_unknown(item)
            if res:
                result.append(res)
    elif isinstance(params, Mapping):
        if params.get('fixture_status!', None) == 'Do not know':
            result = None
        else:
            result = {}
            for key, val in params.items():
                status_key = '{}_status!'.format(key)
                if params.get(status_key) == 'Do not know':
                    res = None
                else:
                    res = remove_unknown(val)
                if res:
                    result[key] = res
    else:
        result = params
    if isinstance(result, Mapping):
        result = {
            key: val for key, val in result.items() if val != 'Do not know'
        }
    return result


def unroll(dct):
    """
    Convert key:subkey to  nested dicts
    e.g.
    {
        'key:subkey1': val1,
        'key:subkey2': val2,
        'otherkey': val3
    }

    converts to
    {
    'key': {
        subkey1': val1,
        'subkey2': val2
    },
    'otherkey': val3
    }
    """
    # build a new dict as _split_key is non-mutating
    result = {}
    for key, val in dct.items():
        key, val = _split_key(result, key, val)
        if isinstance(val, Mapping):
            val = unroll(val)
        elif isinstance(val, Sequence) and not isinstance(val, basestring):
            val = [
                unroll(item) if isinstance(item, Mapping) else item
                for item in val
            ]
        result[key] = val
    return result


class BESError(Exception):
    """Base class for exceptions in the modules"""

    def __init__(self, msg, **kwargs):
        self.message = msg
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        return '<{}: "{}">'.format(self.__class__.__name__, self.message)

    def __str__(self):
        return self.message


class APIError(BESError):
    pass


class BESClient(object):
    """
    API Client for BES API
    """
    # pylint: disable=too-few-public-methods, too-many-instance-attributes

    def __init__(self, email=None, password=None, organization_token=None,
                 access_token=None, user_id=None, base_url=None,
                 api_version=2, timeout=TIMEOUT):
        # pylint: disable=too-many-arguments
        """
        Set up Client:

        Note: You must set base_url to point to the correct url.

        Note for everything you will need to supply email, password and
        organization_token, or access_token (& user_id) in order to
        authenticate. If the former, instantiating a Client will fetch
        an access token and store it as client.token. You can reuse this token
        by supplying it as access_token in order to avoid this step,  as API
        calls are rate limited. If you do this the onus on ensuring the token
        is valid falls to you.

        :param email: api user email
        :type email: str
        :param password: api user password
        :type password: str
        :param password: api user password
        :type email: str
        :param organization_token: api organization token
        :type organization_token: str
        :param access_token: api access token
        :type access_token: str
        :param user_id_token: api user_id token
        :type user_id_token: str
        :param timeout: server timeout in seconds default 0.5
        :type timeout: float
        """
        if not base_url:
            raise APIError('Base url must be supplied')
        else:
            self.base_url = base_url
        if not api_version:
            raise APIError('API version must be supplied')
        else:
            self.api_version = str(api_version)
        self.email = email
        self.password = password
        self.organization_token = organization_token
        self.timeout = timeout
        if access_token:
            self.token = access_token
            self.user_id = user_id
        elif email and password and organization_token:
            self.user_id, self.token = self._authenticate(
                self.email, self.password, self.organization_token
            )

    def _authenticate(self, email, password, organization_token):
        """
        Obtain user id & token
        :param email: api user email
        :type email: str
        :param password: api user password
        :type password: str
        :param password: api user password
        :type email: str
        :param organization_token: api organization token
        :type organization_token: str

        :returns: int, string -- user_id, token
        :raises: APIError
        """
        endpoint = 'users/authenticate'
        params = {
            'email': email,
            'password': password,
            'password_confirmation': password,
            'organization_token': organization_token
        }
        response = self._post(endpoint, **params)
        self._check_call_success(
            response, prefix='Unable to obtain access token'
        )
        user_id = response.json()['user_id']
        token = response.json()['token']
        return user_id, token

    def _check_call_success(self, response, prefix=None, default=None):
        """
        Check if api call was successful.

        Raises APIError on failure. The error msg is derived from the
        error returned by the BES API prefixed by prefix. Default is used
        if not error can be found

        :param response: Requests response object
        :type response: Requests.Response
        :param prefix: Prefixed to error message
        :type prefix: str
        :param default: default error message

        :raises: APIError
        """
        # pylint: disable=no-self-use, no-member
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                error = response.json().get('error')
                if not error:
                    error = response.json().get('errors')
            except ValueError:
                error = response.content
                if isinstance(error, bytes):
                    error = error.decode('utf-8')
                # generic error page
                if error.startswith('<!DOCTYPE html>'):
                    error = None
            if not error:
                error = default
            if isinstance(error, dict):
                error = ", ".join(
                    "{}: {}".format(
                        key,
                        ", ".join(val) if isinstance(val, list) else val
                    ) for key, val in error.items()
                )
            # v1 api dumps stack trace
            if error and '\n' in error:
                error = error.split('\n')[0]
            error = "{} {}".format(response.status_code, error)
            if prefix:
                if not prefix.endswith(':'):
                    prefix = "{}:".format(prefix)
                error = "{} {}".format(prefix, error)
            raise APIError(error, status_code=response.status_code)

    def _construct_payload(self, params, compulsory_params=None):
        """
        Construct parameters for an api call. Adds token automatically.
.
        :param params: An dictionary of key-value pairs to include
            in the request.
        :type params: dict
        :param compulsory_params: params that must be supplied
        :type compulsory_params: list
        :return: A dictionary of k-v pairs to send to the server
            in the request.
        """
        if not params:
            params = {}
        params = _params_from_dict(params, required=compulsory_params)
        if getattr(self, 'token', None):
            params['token'] = self.token
        return params

    def _construct_url(self, endpoint, noid=False, **kwargs):
        """
        Construct URL

        :param endpoint: endpoint
        :type endpoint: Str
        :param noid: allow action without id
        :type noid: bool
        :param base_url: base url (everything up to version no)
        :type base_url: Str
        :param api_version: Api Version, default v2
        :type api_version: Str or Int
        :param id: id to insert in url (optional)
        :type id:  Str or Int
        :param action: append to url after id
        :type action: Str
        """
        action = kwargs.pop('action', None)
        api_id = kwargs.pop('id', None)
        api_version = kwargs.pop('api_version', None)
        base_url = kwargs.pop('base_url', None)

        if action and not api_id and not noid:
            raise BESError('id must be supplied with action')

        action = action.strip('/') if action else None
        api_id = int(api_id) if api_id else None
        api_version = str(api_version) if api_version else self.api_version
        if not api_version.startswith('v'):
            api_version = 'v{}'.format(api_version)
        base_url = base_url.rstrip('/') if base_url else self.base_url

        url = "{}/{}/{}".format(base_url, api_version, endpoint.strip('/'))

        if api_id:
            url = "{}/{}".format(url, api_id)
        if action:
            url = "{}/{}".format(url, action)
        return url

    def _get(self, endpoint, compulsory_params=None, noid=False, **kwargs):
        """Make api calls using GET."""
        url = self._construct_url(endpoint, noid=noid, **kwargs)
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if params:
            payload['params'] = params
        api_call = requests.get(url, **payload)
        return api_call

    def _post(self, endpoint, compulsory_params=None, files=None, **kwargs):
        """Make api calls using POST."""
        url = self._construct_url(endpoint, **kwargs)
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if files:
            payload['files'] = files
        payload['json'] = params
        api_call = requests.post(url, **payload)
        return api_call

    def _put(self, endpoint, compulsory_params=None, files=None,
             use_json=True, **kwargs):
        """Make api calls using PUT."""
        url = self._construct_url(endpoint, **kwargs)
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if files:
            payload['files'] = files
        if use_json:
            payload['json'] = params
        else:
            payload['params'] = params
        api_call = requests.put(url, **payload)
        return api_call

    def _patch(self, endpoint, compulsory_params=None, files=None, **kwargs):
        """
        Make api calls using PATCH.

        N.B. There are currently not BES API calls that use patch
        """
        url = self._construct_url(endpoint, **kwargs)
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if files:
            payload['files'] = files
        payload['json'] = params
        api_call = requests.patch(url, **payload)
        return api_call

    def _delete(self, endpoint, **kwargs):
        """Make api calls using DELETE."""
        url = self._construct_url(endpoint, **kwargs)
        params = self._construct_payload(None)
        payload = {'timeout': self.timeout}
        if params:
            payload['params'] = params
        api_call = requests.delete(url, **payload)
        return api_call

    # Public Methods
    def create_preview_building(self,
                                assessment_type='Test',
                                building_name=None,
                                year_completed=None,
                                floor_area=None,
                                street=None,
                                city=None,
                                state=None,
                                postal_code=None,
                                use_type=None,
                                orientation=None,
                                number_floors=None):
        """
        :param building_name: name of building
        :type building_name: str
        :param year_completed:  year building was completed
        :type year_completed: str
        :param floor_area: gross floor area in square feet
        :type floor_area: str
        :param street: street address
        :type street: str
        :param city: city of address
        :type city: str
        :param state: address state
        :type state: str
        :param postal_code: zip code of address
        :type postal_code: str
        :param assessment_type: 'Test' or 'Real' (if doing formal audit)
        :type assessment_type: str
        :param use_type: building use type see: https://is.gd/gYlBud
        :type use_type: str
        :param orientation: the long side of building
                            ('North/South' or 'East/West')
        :type orientation: str
        :param number_floors: the number of floor in the building.
        :type number_floors: str

        :raises: BESError (inc APIError)
        :returns: building details (inc id).
        :rtype: dict

        Note:: number_floors is not returned in results/reports
        """
        endpoint = 'preview_buildings'
        building = _params_from_dict(locals(), required=locals().keys())
        response = self._post(endpoint, building=building)
        self._check_call_success(
            response, prefix="Unable to create preview building"
        )
        return response.json()

    def delete_preview_building(self, id):
        """
        Delete a preview building

        :param id: id of building
        :type id: int
        :rtype: None
        :raises: APIError
        """
        endpoint = 'preview_buildings'
        response = self._delete(endpoint, id=id)
        self._check_call_success(
            response, prefix="Unable to delete preview building"
        )

    def duplicate_preview_building(self, id):
        """
        Duplicate a preview building

        :param id: id of building
        :type id: int
        :returns: short form report
        :rtype: Dict
        :raises: APIError
        """
        endpoint = 'preview_buildings'
        response = self._get(endpoint, id=id, action='duplicate')
        self._check_call_success(
            response, prefix="Unable to duplicate preview building"
        )
        return response.json()

    def get_preview_building(self, id, report_type=None):
        """
        Get Preview Building Details

        If the report_type is report or pdf (identical) the returned json,
        indicates the preview scores and contains a link to the pdf.
        This is only available for preview building the have had a simulation
        run.

        :param id: id of building
        :type id: int
        :param report_type: report type: 'simple' or 'pdf'/'report') or None
        :type report_type: str
        :returns: preview building details
        :rtype: dict or PDF
        :raises: BESError/APIError
        """
        endpoint = 'preview_buildings'
        params = {'id': id}
        if report_type:
            if report_type not in ['simple', 'pdf', 'report']:
                msg = "report_type must be 'simple', 'report', 'pdf' or None"
                raise BESError(msg)
            if report_type == 'pdf':
                report_type = 'report'
            params['action'] = report_type
        response = self._get(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to get preview building details"
        )
        return response.content if report_type == 'pdf' else response.json()

    def list_preview_buildings(self):
        """
        List preview buildings (belonging to user)

        :raises: APIError
        :returns: list of buildings (simple format)
        :rtype: list
        """
        endpoint = 'preview_buildings'
        response = self._get(endpoint)
        self._check_call_success(
            response, prefix="Unable to list preview buildings"
        )
        return response.json()

    def set_preview_building_status(self, id, status):
        """
        Set  a preview buildings status.

        N.B. This appears in the v2 API docs but only appears to hit 404/500

        Status:     Effect
        'edit_mode'      Sets the building status type back to "Editing"
        'verify'    Sets the attribute certainty status to
                        "Verified" or "Do not know"
        'revert'     Sets the attribute certainty status *from*
                        "Edited" or "Do not know"

        :param id: id of building
        :type id: int
        :param status: one of edit_mode, verify, revert
        :type status: string
        :rtype: None
        :raises: BESError or APIError
        """
        endpoint = 'preview_buildings'
        response = self._put(endpoint, id=id, action=status)
        prefix = "Unable to set preview building {} status to {}".format(
            id, status
        )
        self._check_call_success(response, prefix=prefix)

    def simulate_preview_building(self, id):
        """
        Simulate a building for simulation

        :param id: id of building
        :type id: int
        :returns: Validation description (e.g. Valid)
        :rtype: String
        :raises: APIError
        """
        endpoint = 'preview_buildings'
        response = self._get(endpoint, id=id, action='simulate')
        self._check_call_success(
            response, prefix="Unable to simulate preview building"
        )

    def update_preview_building(self, building_id, block_id,
                                assessment_type=None,
                                name=None,
                                year_of_construction=None,
                                address=None,
                                city=None,
                                state=None,
                                zip_code=None,
                                notes=None,
                                extras=None):
        """
        Update a preview building.

        Note:  Only the following attributes are currently accepted,
        these all refer to the building though a block id is compulsory.
        name is used not building_name.

        It is supposed to be  possible to supply arguments that refer to the
        block, (e.g. 'floor:floor_type') but there is currently a bug
        preventing this (2017-5-10). These should be supplied a dictionary
        to extras (to allow for e.g. "floor:floor_type", representing nested
        data structures).

        :param building_id: id of building
        :type building_id: int
        :param block_id: id of block
        :type block_id: int
        :param name: name of building
        :type name: str
        :param year_of_construction:  year building was constructed
        :type year_of_construction: str
        :param address: street address
        :type address: str
        :param city: city of address
        :type city: str
        :param state: address state
        :type state: str
        :param zip_code: zip code of address
        :type zip_code: str
        :param assessment_type: 'Test' or 'Real' (if doing formal audit)
        :type assessment_type: str
        :param notes: building notes
        :type notes: str
        :param extras: extra arguments representing blocks
        :type extras: dict
        :raises: BESError (inc APIError)
        :returns: building details (long form).
        :rtype: dict
        """
        endpoint = 'preview_buildings'
        building = _params_from_dict(
            locals(), exclude=['building_id', 'extras']
        )
        if extras:
            building.update(extras)
        params = {'building': building}
        response = self._put(endpoint, id=building_id, **params)
        self._check_call_success(
            response, prefix="Unable to update preview building"
        )
        return response.json()

    def validate_preview_building(self, id):
        """
        Validate a preview building

        :param id: id of building
        :type id: int
        :returns: Validation description (e.g. Valid)
        :rtype: String
        :raises: APIError
        """
        endpoint = 'preview_buildings'
        response = self._get(endpoint, id=id, action='validate')
        self._check_call_success(
            response, prefix="Unable to validate preview building"
        )
        return response.content

    def get_user(self, id):
        """
        Get a users details.

        N.B. Users can only access their own accounts

        :param id: id of user
        :type id: int
        :returns: user details
        :rtype: dict
        :raises: BESError/APIError
        """
        endpoint = 'users'
        response = self._get(endpoint, id=id)
        self._check_call_success(response, prefix="Unable to get user details")
        return response.json()

    def update_user(self, id,
                    email=None, password=None, password_confirmation=None,
                    first_name=None, last_name=None):
        """
        Update a users details.

        N.B. Users can only update their own accounts and can not change
        their role or organization

        :param id: id of user
        :type id: int
        :param email: user's email
        :type email: str
        :param password: user's password
        :type password: str
        :param password_confirmation: user password  (repeated)
        :type password_confirmation: str
        :param first_name: user's first name
        :type first_name: str
        :param last_name: user's last name
        :type last_name: str

        :returns: None
        :raises: BESError/APIError
        """
        endpoint = 'users'
        if password and not password_confirmation:
            msg = "Password and password_confirmation must be supplied"
            raise BESError(msg)
        elif password != password_confirmation:
            msg = 'Passwords do not match!'
            raise BESError(msg)
        params = _params_from_dict(locals())
        response = self._put(endpoint, id=id, **params)
        self._check_call_success(
            response, prefix="Unable to update user details"
        )

    # v1 API functionality
    def create_block(self,
                     building_id,
                     shape_id,
                     name,
                     floor_to_floor_height,
                     floor_to_ceiling_height,
                     is_above_ground,
                     number_of_floors,
                     orientation,
                     position,
                     vertices,
                     dimension_1,
                     dimension_2,
                     dimension_3=None,
                     dimension_4=None,
                     dimension_5=None,
                     dimension_6=None,
                     dimension_7=None,
                     dimension_8=None,
                     dimension_9=None,
                     dimension_10=None,
                     building_use_type_id=None,
                     floor_id=None,
                     hvac_system_ez_status_id=None,
                     operation_id=None,
                     operating_season_id=None,
                     orientation_system_ez_status_id=None,
                     roof_id=None,
                     skylight_id=None,
                     skylight_layout_id=None,
                     zone_layout_id=None,
                     co_sensors=None,
                     has_drop_ceiling=None,
                     has_timer_controls=None,
                     has_toplight_control=None,
                     low_flow_faucets=None,
                     percent_footprint=None,
                     perimeter_zone_depth=None,
                     uses_percent_served=None):
        """
        Create a block.

        :param building_id: id of building
        :type building_id: int
        :param shape_id: ID for the shape of this block. required
        :type  shape_id int:
        :param name: custom name for block
        :type name: str
        :param floor_to_floor_height: required Average floor-to-floor height
                                      (in feet). Must be > 9.
        :type  floor_to_floor_height: float:
        :param floor_to_ceiling_height: required, Average floor-to-ceiling
                                        height (in feet). Must be > 0.
        :type  floor_to_ceiling_height: float:
        :param is_above_ground: required True if above, false if below.
        :type is_above_ground bool:
        :param number_of_floors: required  Number of floors in block (1-500).
        :type  number_of_floors: int:
        :param orientation: required Degrees from North of block (0-359).
        :type  orientation: float:
        :param vertices: required x,y coordinates for the block vertices.
        :type  vertices: str:
        :param position: required x,y coordinates of block position.
        :type  position: str:
        :param dimension_1: required Length of dimension 1 (in feet).
        :type  dimension_1: float:
        :param dimension_2: required Length of dimension 2 (in feet).
        :type  dimension_2: float:
        :param dimension_3: optional Length of dimension 3 (in feet).
                            Depends on shape if required.
        :type dimension_3:  float:
        :param dimension_4: optional Length of dimension 4 (in feet).
        :type  dimension_4: float:
        :param dimension_5: optional Length of dimension 5 (in feet).
        :type  dimension_5: float:
        :param dimension_6: optional Length of dimension 6 (in feet).
        :type  dimension_6: float:
        :param dimension_7: optional Length of dimension 7 (in feet).
        :type  dimension_7: float:
        :param dimension_8: optional Length of dimension 8 (in feet).
        :type  dimension_8: float:
        :param dimension_9: optional Length of dimension 9 (in feet).
        :type  dimension_9: float:
        :param dimension_10: optional Length of dimension 10 (in feet).
        :type  dimension_10: float:
        :param building_use_type_id: optional ID of building use type
                                      assigned to block.
        :type building_use_type_id int:
        :param floor_id: optional ID of floor assigned to block.
        :type floor_id int:
        :param hvac_system_ez_status_id: optional ???
        :type hvac_system_ez_status_id int:
        :param operation_id: optional ID of operation assigned to block.
        :type operation_id int:
        :param operating_season_id: optional ID of operating season.
        :type operating_season_id int:
        :param orientation_system_ez_status_id: optional ???
        :type orientation_system_ez_status_id int:
        :param roof_id: optional ID of roof assigned to block.
        :type roof_id int:
        :param skylight_id: optional ID of Skylight assigned to block.
        :type skylight_id int:
        :param skylight_layout_id: optional ID of Skylight layout.
        :type skylight_layout_id int:
        :param zone_layout_id: optional ID of zone layout.
        :type zone_layout_id int:
        :param co_sensors: optional True if CO Sensors, false otherwise.
        :type co_sensors bool:
        :param has_drop_ceiling: optional
        :type has_drop_ceiling bool:
        :param has_timer_controls: optional
        :type has_timer_controls bool:
        :param has_toplight_control: optional ???
        :type has_toplight_control bool:
        :param low_flow_faucets: optional True if low flow faucets used.
        :type low_flow_faucets bool:
        :param percent_footprint: optional Skylight percent of roof area
                                  (usually 3%-5%).
        :type percent_footprint float:
        :param perimeter_zone_depth: optional Perimeter zone depth.
        :type perimeter_zone_depth float:
        :param uses_percent_served: optional True if uses percent served.
        :type uses_percent_served bool:

        :raises: BESError (inc APIError)
        :returns: block details.
        :rtype: dict
        """
        api_version = 1
        endpoint = 'buildings'
        params = _params_from_dict(locals(), exclude='building_id')
        params = _fix_params(params)
        params.update(
            {'api_version': api_version, 'id': building_id, 'action': 'blocks'}
        )
        response = self._post(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to create block"
        )
        return response.json()

    def delete_block(self, id):
        """
        Delete a block by id

        :param id: id of block
        :type id: int
        :rtype: None
        :raises: APIError
        """
        api_version = 1
        endpoint = 'blocks'
        response = self._delete(endpoint, id=id, api_version=api_version)
        self._check_call_success(
            response, prefix="Unable to delete block"
        )

    def get_block(self, id):
        """
        Get a block by id

        :param id: id of block
        :type id: int
        :returns: block info
        :rtype: Dict
        :raises: APIError
        """
        api_version = 1
        endpoint = 'blocks'
        params = {'api_version': api_version}
        response = self._get(endpoint, id=id, **params)
        self._check_call_success(
            response, prefix="Unable to get block"
        )
        return response.json()

    def update_block(self,
                     id,
                     shape_id,
                     name=None,
                     floor_to_floor_height=None,
                     floor_to_ceiling_height=None,
                     is_above_ground=None,
                     number_of_floors=None,
                     position=None,
                     orientation=None,
                     vertices=None,
                     dimension_1=None,
                     dimension_2=None,
                     dimension_3=None,
                     dimension_4=None,
                     dimension_5=None,
                     dimension_6=None,
                     dimension_7=None,
                     dimension_8=None,
                     dimension_9=None,
                     dimension_10=None,
                     building_use_type_id=None,
                     floor_id=None,
                     hvac_system_ez_status_id=None,
                     operation_id=None,
                     operating_season_id=None,
                     orientation_system_ez_status_id=None,
                     roof_id=None,
                     skylight_id=None,
                     skylight_layout_id=None,
                     zone_layout_id=None,
                     co_sensors=None,
                     has_drop_ceiling=None,
                     has_timer_controls=None,
                     has_toplight_control=None,
                     low_flow_faucets=None,
                     percent_footprint=None,
                     perimeter_zone_depth=None,
                     uses_percent_served=None):
        """
        Update an existing block. NOTE: A block's shape can NOT be modified
        once it has been created. If the wrong shape has been selected the
        block must be deleted and recreated.

        :param id: block id, required
        :type id: int
        :param shape_id: ID for the shape of this block. required
        :type shape_id  int:
        :param name: custom name for block
        :type name: str
        :param floor_to_floor_height: required Average floor-to-floor height
                                      (in feet). Must be > 9.
        :type  floor_to_floor_height: float:
        :param floor_to_ceiling_height: required, Average floor-to-ceiling
                                        height (in feet). Must be > 0.
        :type  floor_to_ceiling_height: float:
        :param is_above_ground: required True if above, false if below.
        :type is_above_ground bool:
        :param number_of_floors: required  Number of floors in block (1-500).
        :type  number_of_floors: int:
        :param orientation: required Degrees from North of block (0-359).
        :type  orientation: float:
        :param vertices: required x,y coordinates for the block vertices.
        :type  vertices: str:
        :param position: required x,y coordinates of block position.
        :type  position: str:
        :param dimension_1: required Length of dimension 1 (in feet).
        :type  dimension_1: float:
        :param dimension_2: required Length of dimension 2 (in feet).
        :type  dimension_2: float:
        :param dimension_3: optional Length of dimension 3 (in feet).
                            Depends on shape if required.
        :type dimension_3:  float:
        :param dimension_4: optional Length of dimension 4 (in feet).
        :type  dimension_4: float:
        :param dimension_5: optional Length of dimension 5 (in feet).
        :type  dimension_5: float:
        :param dimension_6: optional Length of dimension 6 (in feet).
        :type  dimension_6: float:
        :param dimension_7: optional Length of dimension 7 (in feet).
        :type  dimension_7: float:
        :param dimension_8: optional Length of dimension 8 (in feet).
        :type  dimension_8: float:
        :param dimension_9: optional Length of dimension 9 (in feet).
        :type  dimension_9: float:
        :param dimension_10: optional Length of dimension 10 (in feet).
        :type  dimension_10: float:
        :param building_use_type_id: optional ID of building use type
                                      assigned to block.
        :type building_use_type_id int:
        :param floor_id: optional ID of floor assigned to block.
        :type floor_id int:
        :param hvac_system_ez_status_id: optional ???
        :type hvac_system_ez_status_id int:
        :param operation_id: optional ID of operation assigned to block.
        :type operation_id int:
        :param operating_season_id: optional ID of operating season.
        :type operating_season_id int:
        :param orientation_system_ez_status_id: optional ???
        :type orientation_system_ez_status_id int:
        :param roof_id: optional ID of roof assigned to block.
        :type roof_id int:
        :param skylight_id: optional ID of Skylight assigned to block.
        :type skylight_id int:
        :param skylight_layout_id: optional ID of Skylight layout.
        :type skylight_layout_id int:
        :param zone_layout_id: optional ID of zone layout.
        :type zone_layout_id int:
        :param co_sensors: optional True if CO Sensors, false otherwise.
        :type co_sensors bool:
        :param has_drop_ceiling: optional
        :type has_drop_ceiling bool:
        :param has_timer_controls: optional
        :type has_timer_controls bool:
        :param has_toplight_control: optional ???
        :type has_toplight_control bool:
        :param low_flow_faucets: optional True if low flow faucets used.
        :type low_flow_faucets bool:
        :param percent_footprint: optional Skylight percent of roof area
                                  (usually 3%-5%).
        :type percent_footprint float:
        :param perimeter_zone_depth: optional Perimeter zone depth.
        :type perimeter_zone_depth float:
        :param uses_percent_served: optional True if uses percent served.
        :type uses_percent_served bool:

        :rtype: None
        :raises: BES/APIError
        """
        api_version = 1
        endpoint = 'blocks'
        params = _params_from_dict(locals())
        params['api_version'] = api_version
        response = self._put(endpoint, id=id, **params)
        self._check_call_success(
            response, prefix="Unable to update block"
        )

    def attach_block_resource(self, block_resource, block_id, resource_id,
                              **kwargs):
        """
        Create a resource and attach it to a block (by block_id).

        e.g. air handler,floor (use create for surface) etc.

        For a full list see BLOCK_RESOURCES &
        https://blockenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resources e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted

        :param block_resource: resource name
        :type block_resource: string
        :param block_id: id of block.
        :type block_id: int
        :param resource_id: id of resource, corresponds to eg. fixture_id
        :type resouce_id: int
        :param kwargs: resource attributes to set
        :type kwargs': str
        :returns: resource
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'blocks'
        # convert to correct format and check validity
        action, resource_name_id = _get_block_resource(block_resource)
        params = _params_from_dict(kwargs)
        params.update({
            'id': block_id, resource_name_id: resource_id,
            'api_version': api_version, 'action': action
        })
        response = self._post(endpoint, **params)
        prefix = "Unable to attach {} to block: {}".format(
            action, block_id
        )
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def create_block_resource(self, block_resource, block_id, name,
                              **kwargs):
        """
        Create a resource and attach it to a block (by block_id).

        Use this for surface, for everything else create the resource,
        then attach it using attach_block_resource

        For a full list see BLOCK_RESOURCES &
        https://blockenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resources e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted

        :param block_resource: resource name
        :type block_resource: string
        :param block_id: id of block.
        :type block_id: int
        :param name: name of resource
        :type name: str
        :param kwargs: resource attributes to set
        :type kwargs: str
        :returns: resource
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'blocks'
        # convert to correct format and check validity
        action, _ = _get_block_resource(block_resource)
        params = _params_from_dict(kwargs)
        params.update({
            'id': block_id, 'api_version': api_version, 'action': action,
            'name': name
        })
        response = self._post(endpoint, **params)
        prefix = "Unable to create {} for block: {}".format(
            action, block_id
        )
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def delete_block_resource(self, block_resource, id):
        """
        Delete a  block resource by id

        e.g. air handler,floor etc.

        For a full list see BLOCK_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resource e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted

        :param block_resource: resource name
        :type block_resource: string
        :param id: id of resource to delete.
        :type id: int (or string)
        :rtype: None
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint, _ = _get_block_resource(block_resource)
        params = {'id': id, 'api_version': api_version}
        response = self._delete(endpoint, **params)
        prefix = "Unable to delete {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)

    def get_block_resource(self, block_resource, id):
        """
        Get a block resource by id

        e.g. air handler,floor etc.

        For a full list see BLOCK_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resource e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted.

        :param block_resource: resource name
        :type block_resource: string
        :param id: id of resource name to retrieve.
        :type id: int (or string)
        :returns: resource
        :rtype: dict
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint, _ = _get_block_resource(block_resource)
        params = {'id': id, 'api_version': api_version}
        response = self._get(endpoint, **params)
        prefix = "Unable to get {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def get_block_resources(self, block_resource, block_id):
        """
        Get all resources belonging to a block by block_id

        e.g. air handler,floor etc.

        For a full list see BLOCK_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resource e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted

        :param block_resource: resource name
        :type block_resource: string
        :param block_id: block_id of building.
        :type block_id: int (or string)
        :returns: list of resource
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'blocks'
        # convert to correct format and check validity
        action, _ = _get_block_resource(block_resource)
        params = {
            'id': block_id, 'api_version': api_version, 'action': action
        }
        response = self._get(endpoint, **params)
        prefix = "Unable to get {} for block: {}".format(
            action, block_id
        )
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def update_block_resource(self, block_resource, block_resource_id,
                              resource_id, **kwargs):
        """
        Update a block resource by id

        e.g. air handler,floor etc.

        For a full list see BLOCK_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience block_resource e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed). block_ at the beginning may be omitted

        :param block_resource: resource name
        :type block_resource: string
        :param block_resource_id: id of block resource to update.
        :type block_resource_id: int (or string)
        :param resource_id: id of resource, corresponds to eg. fixture_id
        :type resouce_id: int
        :rtype: None
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint, resource_name_id = _get_block_resource(block_resource)
        params = _params_from_dict(kwargs)
        params.update({
            'id': block_resource_id, resource_name_id: resource_id,
            'api_version': api_version,
        })
        response = self._put(
            endpoint, **params
        )
        prefix = "Unable to update {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)

    def create_building(self,
                        assessment_type_id,
                        name,
                        year_of_construction,
                        address,
                        city,
                        state,
                        zip_code,
                        reported_floor_area,
                        notes=None):
        """
        Create a building (using v1 api)

        :param assessment_type_id: ???
        :type assessment_type_id: int
        :param name: name of building
        :type name: str
        :param year_of_construction:  year building was constructed
        :type year_of_construction: str
        :param address: street address
        :type address: str
        :param city: city of address
        :type city: str
        :param state: address state
        :type state: str
        :param zip_code: zip code of address
        :type zip_code: str
        :param reported_floor_area:  UNDOCUMENTED,
                                     api docs have total_floor_area,
                                     (Gross floor area in square feet)
                                     but does not set it even with supplied
                                     value
        :type reported_floor_area: int
        :param notes: building notes
        :type notes: str
        :raises: BESError (inc APIError)
        :returns: building details.
        :rtype: dict
        """
        api_version = 1
        endpoint = 'buildings'
        params = _params_from_dict(locals())
        params['api_version'] = api_version
        response = self._post(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to create building"
        )
        return response.json()

    def get_building(self, id, report_type=None):
        """
        Get Building Details

        If report_type is set to 'simple' a simplified data structure lacking
        (some of the) nested info will be returned.

        If report_type is set to 'pdf' a PDF report will be returned.
        See get_pdf for a function that will write this to a file.

        :param id: id of building
        :type id: int
        :param report_type: report type: 'simple' or 'pdf' or None
        :type report_type: str
        :returns:building details
        :rtype: dict or PDF
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'buildings'
        params = {'id': id, 'api_version': api_version}
        if report_type:
            if report_type not in ['simple', 'pdf', 'report']:
                msg = "report_type must be 'simple', 'report', 'pdf' or None"
                raise BESError(msg)
            if report_type == 'pdf':
                report_type = 'report'
            params['action'] = report_type
        response = self._get(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to get building details"
        )
        return response.content if report_type == 'report' else response.json()

    def get_pdf(self, id, filename):
        """Write a copy of the pdf report to filename"""
        report = self.get_building(id, report_type='pdf')
        with open(filename, 'wb') as pdf:
            pdf.write(report)

    def get_building_blocks(self, building_id):
        """
        Get a buildings block

        :param building_id: id of building
        :type building_id: int
        :returns: blocks
        :rtype: list
        :raises: APIError
        """
        api_version = 1
        endpoint = 'buildings'
        params = {
            'api_version': api_version, 'id': building_id, 'action': 'blocks'
        }
        response = self._get(endpoint, **params)
        prefix = "Unable to get blocks for building {}".format(building_id)
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def get_building_resources(self, resource_name, building_id):
        """
        Get all resources belonging to a building by building_id

        e.g. air handler,floor etc.

        For a full list see BES_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience resource_name e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed).

        :param resource_name: resource name
        :type resource_name: string
        :param building_id: building_id of building.
        :type building_id: int (or string)
        :returns: list of resource
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'buildings'
        # convert to correct format and check validity
        action = _get_resource_name(resource_name)
        params = {
            'id': building_id, 'api_version': api_version, 'action': action
        }
        response = self._get(endpoint, **params)
        prefix = "Unable to get {} for building: {}".format(
            action, building_id
        )
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def get_building_score(self, id):
        """
        Get the Building's Energy Score

        If a simulation has not been run this will 404

        Only works on 'Full' buildings; preview buildings will raise 500 error.
        """
        # UNVERIFIED - 404/500
        api_version = 1
        endpoint = 'buildings'
        params = {'id': id, 'api_version': api_version, 'action': 'score'}
        response = self._get(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to get building score"
        )
        return response.json()

    def list_buildings(self):
        """
        List Buildings

        :returns: building list
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'buildings'
        params = {'api_version': api_version}
        response = self._get(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to list buildings"
        )
        return response.json()

    def manage_buildings(self, *args):
        """
        Download Simulation Results

        A comma-separated value (.csv) file that includes the current and
        potential scores and energy use data for a building or group of
        buildings.

        :param building_ids: list of building_ids
        :type building_ids: list
        """
        api_version = 1
        endpoint = 'manage_buildings'
        building_ids = [str(building_id) for building_id in args]
        building_ids = ','.join(building_ids)
        params = {
            'action': 'csv', 'api_version': api_version,
            'building_ids': building_ids
        }
        response = self._get(endpoint, noid=True, **params)
        self._check_call_success(
            response, prefix="Unable to retrieve simulation results"
        )
        return response.content

    def simulate_building(self, id):
        """
        Submit a building for simulation (also validates)

        Note raises 404 on error not 500 etc

        :param id: id of building
        :type id: int
        :rtype: None
        :raises: APIError
        """
        api_version = 1
        endpoint = 'buildings'
        params = {'id': id, 'api_version': api_version, 'action': 'simulate'}
        response = self._post(endpoint, **params)
        self._check_call_success(
            response, prefix="Unable to submit building for simulation"
        )

    def update_building(self,
                        id,
                        name=None,
                        year_of_construction=None,
                        address=None,
                        city=None,
                        state=None,
                        zip_code=None,
                        notes=None):
        """
        Update  a building (using v1 api)
        :param id: building id
        :type id: int
        :param name: name of building
        :type name: str
        :param year_of_construction:  year building was constructed
        :type year_of_construction: str
        :param address: street address
        :type address: str
        :param city: city of address
        :type city: str
        :param state: address state
        :type state: str
        :param zip_code: zip code of address
        :type zip_code: str
        :param notes: building notes
        :type notes: str
        :raises: BESError (inc APIError)
        :raises: BESError (inc APIError)
        :rtype: None
        """
        api_version = 1
        endpoint = 'buildings'
        params = _params_from_dict(locals())
        params['api_version'] = api_version
        response = self._put(endpoint, id=id, **params)
        self._check_call_success(
            response, prefix="Unable to update building"
        )

    def validate_building(self, id):
        """
        Validate a Building. Returns True if valid otherwise raises
        exception.

        :param id: id of building to validate.
        :type id: int
        :returns: True if valid
        :rtype: True
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'buildings'
        params = {'id': id, 'api_version': api_version, 'action': 'validate'}
        response = self._get(endpoint, **params)
        valid = response.json()['valid']
        if not valid:
            errors = response.json().get('errors')
            msg = 'Unable to validate building {}: {}'.format(
                id, ", ".join(errors)
            )
            raise APIError(msg)
        return True

    def create_resource(self, resource_name, building_id, **kwargs):
        """
        Create a resource and attach it to a building (by building_id).

        e.g. air handler,floor etc.

        For a full list see BES_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience resource_name e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed).

        :param resource_name: resource name
        :type resource_name: string
        :param building_id: building_id of building.
        :type building_id: int (or string)
        :param kwargs: resource attributes to set
        :type kwargs': str
        :returns: resource
        :rname: list
        :raises: BESError/APIError
        """
        api_version = 1
        endpoint = 'buildings'
        # convert to correct format and check validity
        action = _get_resource_name(resource_name)
        params = _params_from_dict(kwargs)
        params.update({
            'id': building_id, 'api_version': api_version, 'action': action
        })
        response = self._post(endpoint, **params)
        prefix = "Unable to get {} for building: {}".format(
            action, building_id
        )
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def delete_resource(self, resource_name, id):
        """
        Delete a resource by id

        e.g. air handler,floor etc.

        For a full list see BES_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience resource_name e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed).

        :param resource_name: resource name
        :type resource_name: string
        :param id: id of resource to delete.
        :type id: int (or string)
        :rtype: None
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint = _get_resource_name(resource_name)
        params = {'id': id, 'api_version': api_version}
        response = self._delete(endpoint, **params)
        prefix = "Unable to delete {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)

    def get_resource(self, resource_name, id):
        """
        Get a resource by id

        e.g. air handler,floor etc.

        For a full list see BES_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience resource_name e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed).

        :param resource_name: resource name
        :type resource_name: string
        :param id: id of resource name to retrieve.
        :type id: int (or string)
        :returns: resource
        :rtype: dict
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint = _get_resource_name(resource_name)
        params = {'id': id, 'api_version': api_version}
        response = self._get(endpoint, **params)
        prefix = "Unable to get {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def update_resource(self, resource_name, id, **kwargs):
        """
        Update a resource by id

        e.g. air handler,floor etc.

        For a full list see BES_RESOURCES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        For convenience resource_name e.g. air_handler, 'air handler'
        will be converted (ie. spaces will be converted to underscores
        and the value will be converted to lower case and pluralized
        if needed).

        :param resource_name: resource name
        :type resource_name: string
        :param id: id of resource to update.
        :type id: int (or string)
        :rtype: None
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint = _get_resource_name(resource_name)
        params = _params_from_dict(kwargs)
        response = self._put(
            endpoint, id=id, api_version=api_version, **params
        )
        prefix = "Unable to update {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)

    def get_resource_type(self, resource_type, id):
        """
        Get a resource type by id

        e.g. air handler type, boiler type.

        For a full list see BES_RESOURCE_TYPES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        Most of these correspond to an api call such as air_handler_types,
        but there are exceptions. Anything that is immutable is treated
        as a resource type e.g. fan control, window layouts.
        Thus building_use_type is not included.
        For the resource type you should specify 'air_handler'.
        However, for convenience e.g. air_handler_types, 'air handler'
        will be converted (ie. types will be stripped, spaces will be
        converted to underscores and the value will be converted to
        lower case).

        :param resource_type: resource type
        :type resource_type: string
        :param id: id of resource type to retrieve.
        :type id: int (or string)
        :returns: resource description
        :rtype: dict
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint = _get_resource_type(resource_type)
        params = {'id': id, 'api_version': api_version}
        response = self._get(endpoint, **params)
        prefix = "Unable to get {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)
        return response.json()

    def list_resource_types(self, resource_type):
        """
        Get all resource types

        e.g. air handler type, boiler type.

        For a full list see BES_RESOURCE_TYPES &
        https://buildingenergyscore.energy.gov/apidoc/v1.html

        Most of these correspond to an api call such as air_handler_types,
        but there are exceptions. Anything that is immutable is treated
        as a resource type e.g. fan control, window layouts.
        Thus building_use_type is not included.
        For the resource type you should specify 'air_handler'.
        However, for convenience e.g. air_handler_types, 'air handler'
        will be converted (ie. types will be stripped, spaces will be
        converted to underscores and the value will be converted to
        lower case).

        :param resource_type: resource type
        :type resource_type: string
        :returns: resource description
        :rtype: list
        :raises: BESError/APIError
        """
        api_version = 1
        # convert to correct format and check validity
        endpoint = _get_resource_type(resource_type)
        params = {'api_version': api_version}
        response = self._get(endpoint, **params)
        prefix = "Unable to get {}".format(endpoint)
        self._check_call_success(response, prefix=prefix)
        return response.json()
