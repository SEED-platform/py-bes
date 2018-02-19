#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved
..codeauthor::Fable Turas <fable@raintechpdx.com>

Utility functions for Building Energy Asset Score processing
"""

# Imports from Standard Library
from typing import Mapping, Optional, Sequence, Union

# Local Imports
from pybes.pybes import BESClient
from pybes.utils.bes_constants import ASSET_SCORE_PROPERTY_TYPE

# Setup
# Constants
# Data Structure Definitions
# Private Functions


# Public Classes and Functions
def get_full_bldg_status_map(**bes_kwargs):
    # type: () -> Mapping
    """Get mapping of status_type_id to status name from BES"""
    client = BESClient(**bes_kwargs)
    status_types = client.list_resource_types('status')
    return {status['id']: status['display_name'] for status in status_types}


def convert_bes_year(year):
    # type: (Union[str, int]) -> Union[str, int]
    """
    Convert any year_built less than 1900 to 1900 for asset score compatibility
    """
    if year:
        if int(year) < 1900:
            year = 1900
    return year


def get_bes_property_type(value):                           # pragma: no cover
    # type: (str) -> str
    """
    Replace self-selected property types with types expected by asset score.
    """
    return ASSET_SCORE_PROPERTY_TYPE.get(value) or value


def get_addr_line_str(addr_dict, addr_parts=None):
    # type: (Mapping[str, str], Optional[Sequence]) -> str
    """Get address 'line' elements as a single string.

    Combines 'address_line_1' and 'address_line_2' elements as a single string
    to ensure no data is lost and line_2 can be processed according to a
    standard set of rules.

    :param addr_dict: dict containing keys 'address_line_1', 'address_line_2'.
    :type addr_dict: Mapping
    :param addr_parts: optional sequence of address elements
    :type addr_parts:
    :return: string combining 'address_line_1' & 'address_line_2' values.
    :rtype: str
    """
    if not addr_parts:
        addr_parts = ['address_line_1', 'address_line_2']
    if not isinstance(addr_parts, (list, tuple)):
        raise TypeError('addr_parts must be a list or tuple')
    addr_str = ' '.join(str(addr_dict[elem]) for elem in addr_parts
                        if addr_dict.get(elem))
    return addr_str
