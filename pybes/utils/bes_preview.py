#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved
..codeauthor::Fable Turas <fable@raintechpdx.com>

Functionality for processing SEED records into BES and updating SEED with
BES report results.
"""
# Imports from Standard Library
import logging
from typing import Any, Dict, Mapping, Optional, Tuple, Union

# Imports from Third Party Modules
from frozendict import frozendict

# Local Imports
from pybes.pybes import BESClient, BESError
from pybes.utils.bes_utils import (
    convert_bes_year,
    get_addr_line_str,
    get_bes_property_type,
)

# Constants

log = logging.getLogger(__name__)            # pylint: disable-msg=invalid-name


# Private Functions
def _create_bes_preview_payload(property_view):
    # type: (Mapping) -> Dict[Union[str, Any], Union[str, Any]]
    """Create payload matching values from SEED to inputs for BES"""
    state = property_view['state']
    extra_data = state['extra_data']

    year_completed = extra_data.get('year_completed') or state['year_built']
    year_completed = convert_bes_year(year_completed)

    assessment_type = extra_data.get('assessment_type') or 'Real'
    property_type = get_bes_property_type(state['property_type'])
    orientation = extra_data.get('orientation') or 'North/South'

    payload = {
        'building_name': state['property_name'],
        'year_completed': str(year_completed),
        'floor_area': state['gross_floor_area'],
        'street': get_addr_line_str(state),
        'city': state['city'],
        'state': state['state'],
        'postal_code': state['postal_code'],
        'assessment_type': assessment_type,
        'use_type': property_type,
        'orientation': orientation,
        'number_floors': extra_data.get('number_floors')
    }
    return payload


def _validate_bes_payload(payload):
    # type: (Mapping) -> bool
    """Validate payload for bes preview"""
    payload_is_valid = False
    if payload and all(payload.values()):
        payload_is_valid = True
    return payload_is_valid


# Public Functions

def create_bes_preview_bldg_from_seed(client, property_view):
    # type: (BESClient, Mapping) -> Mapping
    """Create new bes preview building from SEED PropertyView"""
    payload = _create_bes_preview_payload(property_view)
    if not _validate_bes_payload(payload):
        msg = "One or more required values are Null: {}".format(payload)
        raise ValueError(msg)
    return client.create_preview_building(**payload)


def initiate_preview_simulation(client, building_id, logger=log):
    # type: (BESClient, int) -> str
    """Initiate BES simulation for BES building matching building_id"""
    if not building_id or not isinstance(building_id, int):
        msg = "building_id must be an integer"
        raise ValueError(msg)
    try:
        client.validate_preview_building(building_id)
        client.simulate_preview_building(building_id)
    except BESError as err:
        msg = "Error validating or simulating: {}, Asset Score ID: {}".format(
            err, building_id
        )
        logger.error(msg)
    return client.get_preview_building(building_id)['status!']


def get_bes_preview_report(client, building_id, status=None, logger=log):
    # type: (BESClient, int, Optional[str]) -> Tuple[Mapping, str]
    """Get full report (long form and scores) from BES for 'Rated' building"""
    complete_report = None
    if not status:
        status = client.get_preview_building(building_id)['status!']
    if status != 'Running' and status != 'Rated':
        status = initiate_preview_simulation(
            client, building_id, logger=logger
        )

    if status == 'Rated':
        try:
            score_report = client.get_preview_building(
                building_id, report_type='pdf'
            )
            pdf_url = score_report.pop('pdf_url', None)
            score_report.pop('name', None)
            score_report.pop('id', None)
            additional_facts = {
                'bes_type': 'Preview',
                'bes_building_id': building_id,
                'bes_status': status,
                'pdf_url': pdf_url,
            }

            complete_report = client.get_building(building_id)
            complete_report.update(additional_facts)
            complete_report.update(score_report)
            complete_report = frozendict(complete_report)
        except BESError as err:
            msg = (
                "Error getting score for preview building: {}, "
                "Asset Score ID: {}".format(err, building_id)
            )
            logger.error(msg)
    return complete_report, status
