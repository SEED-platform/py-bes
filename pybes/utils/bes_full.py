#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved
..codeauthor::Fable Turas <fable@raintechpdx.com>

Functions for getting report and details from BES 'Full' buildings
"""

# Imports from Standard Library
import logging
from typing import Dict, List, Mapping, Optional, Tuple

# Imports from Third Party Modules
from frozendict import frozendict
from requests.exceptions import ReadTimeout

# Local Imports
from pybes.pybes import BESClient, BESError
from pybes.utils.bes_constants import IncompleteBldg
from pybes.utils.bes_preview import get_bes_preview_report
from pybes.utils.bes_utils import get_full_bldg_status_map

# Setup

# Constants
log = logging.getLogger(__name__)            # pylint: disable-msg=invalid-name


# Data Structure Definitions


# Private Functions

def _get_full_bldg_pdf_url(building_id, base_url):
    # type: (int, str) -> str
    """Get report pdf url for full buildings

    BES does not include the url to the report.pdf in the score response for
    v1 full buildings, but does follow a consistent pattern for url creation
    in relation to the production or sandbox api url.
    ie: https://api.labworks.org/buildings/{building id}/report.pdf or
    https://buildingenergyscore.energy.gov/buildings/{building id}/report.pdf
    """
    pdf_url_format = "{}/buildings/{}/report.pdf"
    base_url = base_url.rstrip('/api')
    return pdf_url_format.format(base_url, building_id)


def _get_property_type(bes_building):
    # type: (Dict) -> str
    """Get property type from BES building"""
    property_type = None
    use_types = bes_building.get('use_types')
    if use_types:
        property_type = use_types[0].get('display_name')
    return property_type


# Public Classes and Functions

def initiate_full_simulation(client, building_id, status_map=None,
                             logger=log, **bes_kwargs):
    # type: (BESClient, int) -> str
    """Initiate BES simulation for BES building matching building_id"""
    if not status_map:
        status_map = get_full_bldg_status_map(**bes_kwargs)
    if not building_id or not isinstance(building_id, int):
        msg = "building_id must be an integer"
        raise ValueError(msg)
    try:
        client.validate_building(building_id)
        client.simulate_building(building_id)
    except BESError as err:
        msg = 'Error validating or simulating: {}'.format(err)
        logger.error(msg)
    status_id = client.get_building(building_id)['status_type_id']
    return status_map.get(status_id)


def get_bes_full_report(client, building, status_map=None,
                        logger=log, **bes_kwargs):
    # type: (BESClient, Dict) -> Tuple[Mapping, str]
    """Get full report (long form and scores) from BES for 'Rated' building"""
    complete_report = None
    building_id = building.get('id')
    if not status_map:
        status_map = get_full_bldg_status_map(**bes_kwargs)
    status = status_map.get(building['status_type_id'])

    if status != 'Running' and status != 'Rated':
        status = initiate_full_simulation(
            client, building_id, status_map=status_map, logger=logger
        )

    if status == 'Rated':
        try:
            score_report = client.get_building_score(building_id)
            pdf_url = _get_full_bldg_pdf_url(
                building_id, bes_kwargs['base_url']
            )
            number_floors = len(building['floors'])

            additional_facts = {
                'pdf_url': pdf_url,
                'number_floors': number_floors,
                'property_type': _get_property_type(building),
                'bes_type': 'Full',
                'bes_building_id': building_id,
                'bes_status': status
            }

            complete_report = building.copy()
            complete_report.update(additional_facts)
            complete_report.update(score_report.get('score', {}))
            complete_report = frozendict(complete_report)
        except BESError as err:
            msg = "Error getting score for full building: {}".format(err)
            logger.error(msg)
    return complete_report, status


def get_bes_buildings(incomplete, bes_ids=None, full_bldg=False,
                      status_map=None, logger=log, **bes_kwargs):
    # type: (list, Optional[List[int]]) -> Dict
    """Get buildings with score report from BES api"""
    if not status_map:
        status_map = get_full_bldg_status_map(**bes_kwargs)
    bes_preview_ids = []
    bes_buildings = []
    client = BESClient(**bes_kwargs)
    if bes_ids:
        bes_buildings = []
        for bldg_id in bes_ids:
            if full_bldg:
                bes_buildings.append(client.get_building(bldg_id))
            else:
                bes_buildings.append(client.get_preview_building(bldg_id))
                bes_preview_ids = bes_ids
    else:
        try:
            bes_buildings = client.list_buildings()

            bes_preview_bldgs = client.list_preview_buildings()
            bes_preview_ids = [
                bldg['building_id'] for bldg in bes_preview_bldgs
            ]
        except (BESError, ReadTimeout) as err:
            msg = 'Error downloading: {}'.format(err)
            log.error(msg)
    for bldg in bes_buildings:
        try:
            bldg_id = bldg['id']
            status = status_map.get(bldg['status_type_id'])
        except KeyError:
            bldg_id = bldg['building_id']
            status = bldg['status!']
        if bldg_id in bes_preview_ids:
            building, status = get_bes_preview_report(
                client, bldg_id, status=status, logger=logger
            )
            bes_type = 'Preview'
        else:
            building, status = get_bes_full_report(
                client, bldg, status_map=status_map, logger=logger,
                **bes_kwargs
            )
            bes_type = 'Full'

        if not building:
            incomplete_bldg = IncompleteBldg(
                bldg_id=bldg_id, bldg_type=bes_type, status=status
            )
            incomplete.append(incomplete_bldg)
        else:
            yield building, bes_type
