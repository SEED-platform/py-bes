#!/usr/bin/env python
# encoding: utf-8
"""
copyright (c) 2016-2017 Earth Advantage.
All rights reserved
..codeauthor::Fable Turas <fable@raintechpdx.com>
"""

# Imports from Standard Library
from collections import namedtuple

IncompleteBldg = namedtuple(
    'IncompleteBldg', ('bldg_id', 'bldg_type', 'status')
)

ADDRESS_FIELDS = [
    'address_line_1', 'address_line_2', 'city', 'state', 'postal_code'
]

UPDATE_FIELDS_TO_EXCLUDE = (
    'status_type_id', 'id', 'address', 'zip_code', 'state', 'user_id',
    'year_of_construction', 'total_floor_area', 'name', 'city', 'updated_at'
)
PREVIEW_PAYLOAD_KEYS = (
    'building_name', 'year_completed', 'floor_area', 'street', 'city',
    'state', 'postal_code', 'assessment_type', 'use_type',
    'orientation', 'number_floors',
)

BES_FIELDS_TO_EXCLUDE = (
    'status_type_id', 'id', 'user_id',
)

BES_REPORT_KEYS = (
    'address', 'city', 'state', 'zip_code', 'id', 'name', 'user_id',
    'status_type_id', 'created_at', 'updated_at', 'year_of_construction',
    'total_floor_area', 'use_types', 'blocks', 'roofs', 'walls', 'floors',
    'windows', 'skylights', 'fixtures', 'water_heaters', 'air_handlers',
    'zone_equipments', 'operations', 'plants', 'ratings', 'notes',
    'pdf_url', 'bes_building_id', 'bes_type', 'bes_status',
    'property_type'
)
FULL_SCORE_KEYS = (
    'source_norm_eui', 'source_points', 'potential_eui',
    'potential_points', 'source_eui', 'potential_norm_eui'
)
PREVIEW_SCORE_KEYS = (
    'mean_eui', 'high_score', 'potential_energy_savings', 'min_eui',
    'low_score', 'potential_low_score', 'max_eui', 'potential_high_score'
)
BES_FULL_REPORT_KEYS = set(BES_REPORT_KEYS + FULL_SCORE_KEYS)
BES_PREVIEW_REPORT_KEYS = set(BES_REPORT_KEYS + PREVIEW_SCORE_KEYS)
ADDRESS_MAP = {
    'address_line_1': 'address',
    'city': 'city',
    'state': 'state',
    'postal_code': 'zip_code'
}

PROPERTY_STATE_MAP = {
    'property_name': 'name',
    'property_notes': 'notes',
    'year_built': 'year_of_construction',
    'gross_floor_area': 'total_floor_area',
    'property_type': 'property_type'
}

FIELD_MAPS = {
    'address_mapping': ADDRESS_MAP,
    'property_state_mapping': PROPERTY_STATE_MAP
}

ASSET_SCORE_PROPERTY_TYPE = {
    "Adult Education": "Education",
    "Aquarium": None,
    "Bank Branch": "Office",
    "Bar/Nightclub": "Retail",
    "Barracks": "Lodging",
    "College/University": "Education",
    "Convenience Store with Gas Station": "Retail",
    "Convenience Store without Gas Station": "Retail",
    "Courthouse": "Courthouse",
    "Data Center": None,
    "Distribution Center": "Post Office",
    "Drinking Water Treatment & Distribution": None,
    "Enclosed Mall": "Retail",
    "Energy/Power Station": None,
    "Financial Office": "Office",
    "Fire Station": "Police Station",
    "Food Sales": None,
    "Food Service": None,
    "Hospital (General Medical & Surgical)": None,
    "Hotel": "Lodging",
    "Ice/Curling Rink": None,
    "Indoor Arena": "Community Center",
    "K-12 School": "Education",
    "Laboratory": None,
    "Library": "Library",
    "Lifestyle Center": "Senior Center",
    "Mailing Center/Post Office": "Post Office",
    "Manufacturing/Industrial Plant": None,
    "Medical Office": "Medical Office",
    "Mixed Use Property": None,
    "Movie Theater": "Community Center",
    "Multifamily Housing": "Multi-family (4 floors or greater)",
    "Museum": "Community Center",
    "Non-Refrigerated Warehouse": "Warehouse non-refrigerated",
    "Office": "Office",
    "Other - Education": "Education",
    "Other - Entertainment/Public Assembly": "Community Center",
    "Other - Lodging/Residential": "Lodging",
    "Other - Office": "Office",
    "Other - Other": None,
    "Other - Public Service": "City Hall",
    "Other - Recreation": "Community Center",
    "Other - Restaurant/Bar": None,
    "Other - Retail/Mall": "Retail",
    "Other - Services": "Retail",
    "Other - Specialty Hospital": None,
    "Other - Stadium": None,
    "Other - Technology/Science": "Office",
    "Other - Utility": None,
    "Outpatient Rehabilitation/Physical Therapy": "Medical Office",
    "Parking": "parking-garage",
    "Performing Arts": "Community Center",
    "Personal Services (Health/Beauty, Dry Cleaning, etc)": "Retail",
    "Police Station": "Police Station",
    "Pre-school/Daycare": "Education",
    "Prison/Incarceration": "Police Station",
    "Race Track": None,
    "Refrigerated Warehouse": None,
    "Repair Services (Vehicle, Shoe, Locksmith, etc)": "Retail",
    "Residence Hall/Dormitory": "Lodging",
    "Residential Care Facility": "Assisted Living Facility",
    "Restaurant": None,
    "Retail Store": "Retail",
    "Roller Rink": "Community Center",
    "Self-Storage Facility": "Warehouse non-refrigerated",
    "Senior Care Community": "Assisted Living Facility",
    "Single Family Home": None,
    "Social/Meeting Hall": "Community Center",
    "Stadium (Closed)": None,
    "Stadium (Open)": None,
    "Strip Mall": "Retail",
    "Supermarket/Grocery Store": None,
    "Swimming Pool": None,
    "Transportation Terminal/Station": None,
    "Urgent Care/Clinic/Other Outpatient": "Medical Office",
    "Veterinary Office": "Medical Office",
    "Vocational School": "Education",
    "Wastewater Treatment Plant": None,
    "Wholesale Club/Supercenter": "Retail",
    "Worship Facility": "Religious Building",
    "Zoo": None,
}

SEED_STATE_FIELDS = (
    'import_file',
    'source_type',
    'organization',
    'data_state',
    'merge_state',
    'confidence',
    'jurisdiction_property_id',
    'custom_id_1',
    'pm_parent_property_id',
    'pm_property_id',
    'home_energy_score_id',
    'lot_number',
    'property_name',
    'address_line_1',
    'address_line_2',
    'normalized_address',
    'city',
    'state',
    'postal_code',
    'building_count',
    'property_notes',
    'property_type',
    'year_ending',
    'use_description',
    'gross_floor_area',
    'year_built',
    'recent_sale_date',
    'conditioned_floor_area',
    'occupied_floor_area',
    'owner',
    'owner_email',
    'owner_telephone',
    'owner_address',
    'owner_city_state',
    'owner_postal_code',
    'energy_score',
    'site_eui',
    'generation_date',
    'release_date',
    'source_eui_weather_normalized',
    'site_eui_weather_normalized',
    'source_eui',
    'energy_alerts',
    'space_alerts',
    'building_certification',
    'extra_data',
)
