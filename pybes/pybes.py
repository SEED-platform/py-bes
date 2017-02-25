#!/usr/bin/env python
"""
copyright (c) 2016 Earth Advantage. All rights reserved.
..codeauthor::Paul Munday <paul@paulmunday.net>

BES API Client"""


# Imports from Standard Library

# Imports from External Modules
import requests

# Config/Constants
BASE_URL = 'https://buildingenergyscore.energy.gov/api'
API_VERSION = 'v2'

# http://docs.python-requests.org/en/master/user/quickstart/#timeouts
TIMEOUT = 0.5

# Private Functions and Classes


# Public Functions and Classes
class BESError(Exception):
    """Base class for exceptions in the modules"""
    def __init__(self, msg,  **kwargs):
        self.msg = msg
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def __repr__(self):
        return '<{}: "{}">'.format(self.__class__.__name__, self.msg)

    def __str__(self):
        return self.msg


class APIError(BESError):
    pass


class BESClient(object):
    """
    API Client for BES API
    """
    # pylint: disable=too-few-public-methods, too-many-instance-attributes

    def __init__(self, email=None, password=None, organization_token=None,
                 timeout=TIMEOUT):
        # pylint: disable=too-many-arguments
        """
        Set up Client:

        Note for everything except setting up a user you will need to supply
        email, password and organization_token in order to authenticate.

        :param email: api user email
        :type email: str
        :param password: api user password
        :type password: str
        :param password: api user password
        :type email: str
        :param organization_token: api organization token
        :type organization_token: str
        :param timeout: server timeout in seconds default 0.5
        """
        self.email = email
        self.password = password
        self.organization_token = organization_token
        self.user_id, self.token = self._authenticate(
            self.email, self.password, self.organization_token
        )
        self.timeout = timeout
        self.url = "{}/{}/".format(BASE_URL, API_VERSION)

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
        :raises: API Error
        """
        user_id = None
        token = None
        if email and password and organization_token:
            params = {
                'email': email,
                'password': password,
                'password_confirmation': password,
                'organization_token': organization_token
            }
            response = self.post(
                endpoint='users/authenticate', **params
            )
            self.check_call_success(
                response, prefix='Unable to obtain access token'
            )
            user_id = response.json()['user_id']
            token = response.json()['token']
        return user_id, token

    def check_call_success(self, response, prefix=None, default=None):
        """
        Check if api call was successful.

        Raises APIError on failure. The error msg is derived from the
        error returned by the BES API prefixed by prefix. Default is used
        if not error can be found

        :param response: Requests response object
        :type response: Requests.Response
        :param prefix: Prefixed to error message
        :type prefix: str
        :param default: default error messagee

        :raises: APIError
        """
        # pylint: disable=no-self-use, no-member
        if not response.status_code == requests.codes.ok:
            try:
                error = response.json()['error']
            except (KeyError, ValueError):
                error = default
            if prefix:
                error = "{} {}".format(prefix, error)
            raise APIError(error)

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
        if compulsory_params:
            missing = []
            for param in compulsory_params:
                if param not in params:
                    try:
                        params[param] = getattr(self, param)
                    except AttributeError:
                        missing.append(param)
            if missing:
                msg = "{} {} compulsory field{}".format(
                    ", ".join(missing),
                    'are' if len(missing) > 1 else 'is a',
                    's' if len(missing) > 1 else '',
                )
                raise APIError(msg)
        if self.token:
            params['token'] = self.token
        return params

    def get(self, endpoint, compulsory_params=None, **kwargs):
        """Make api calls using GET."""
        url = self.url + endpoint
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if params:
            payload['params'] = params
        api_call = requests.get(url, **payload)
        return api_call

    def post(self, endpoint, compulsory_params=None, files=None, **kwargs):
        """Make api calls using POST."""
        url = self.url + endpoint
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        if files:
            payload['files'] = files
        payload['json'] = params
        api_call = requests.post(url, **payload)
        return api_call

    def put(self, endpoint, compulsory_params=None, files=None, **kwargs):
        """Make api calls using PUT."""
        url = self.url + endpoint
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        api_call = requests.put(url, **payload)
        if files:
            payload['files'] = files
        payload['json'] = params
        api_call = requests.put(url, **payload)
        return api_call

    def patch(self, endpoint, compulsory_params=None, files=None, **kwargs):
        """
        Make api calls using PATCH.

        N.B. There are currently not BES API calls that use patch
        """
        url = self.url + endpoint
        params = self._construct_payload(
            kwargs, compulsory_params=compulsory_params
        )
        payload = {'timeout': self.timeout}
        api_call = requests.patch(url, **payload)
        if files:
            payload['files'] = files
        payload['json'] = params
        api_call = requests.patch(url, **payload)
        return api_call

    def delete(self, endpoint=None):
        """Make api calls using DELETE."""
        url = self.url + endpoint
        params = self._construct_payload(None)
        payload = {'timeout': self.timeout}
        if params:
            payload['params'] = params
        api_call = requests.delete(url, **payload)
        return api_call


def create_api_user(email, password, organization_token):
    # type(str, str, str) -> int, int, int
    """
    Create a new API user account.

    :param email: user email
    :type email: str
    :param password: user password
    :type password: str
    :param organization_token: organization token
    :type organization_token: str

    :returns: int, int, int -- id, organization_id, role_id
    :raises: APIError
    """
    client = BESClient()
    response = client.post(
        'users',
        email=email,
        password=password,
        password_confirmation=password,
        organization_token=organization_token,
    )
    client.check_call_success(response, prefix="Unable to create user.")
    user_id = response.json()['id']
    org_id = response.json()['organization_id']
    role_id = response.json()['role_id']
    return user_id, org_id, role_id
