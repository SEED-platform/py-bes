Py-BES
======

A Python client for accessing the Building Energy Asset Score API


Documentation
-------------

This is a Python client for accessing the U.S. Department of Energy’s
Building Energy Asset Score API. This is "a national standardized tool
for assessing the physical and structural energy efficiency of commercial
and multifamily residential buildings."

Note this is not a publically accessible API, you will neeed to sign up as a
user and request an API key. You will also need the username and password, for
that user as well as the organization token. See:

* https://buildingenergyscore.energy.gov/
* https://buildingenergyscore.energy.gov/d/users/sign_up
* https://buildingenergyscore.energy.gov/api

This tool concentrates on the Preview Building API (API v2), though some
functionality has been provided for the v1 API.

Note the API requires a user_id and access_token to authenticate. These
can be supplied as parameters when you initialize the client but this is
not necessary if you supply your username and password to the client as it
will fetch one when it initializes. This is the recommended route (as long
as you are reusing the client).

Installation
------------

``pip install py-bes``


Usage:
------
Here is an example that will take you through a basic workflow of

1. Setting up an api user
2. Instatiating the client to connect to the API
3. Creating a preview building
4. Editing that building
5. Running the simulation and getting the results


.. code-block:: python

    ORG_TOKEN = your org token
    EMAIL = email associated with account
    PASSWORD = password associated with account
    FIRST_NAME = first name associated with account
    LAST_NAME = last name associated with account
    BASE_URL = 'https://api.labworks.org/api'   # test sandbox


## create a new api user (one time only)


.. code-block:: python

    create_api_user(
      ORG_TOKEN, EMAIL, PASSWORD, PASSWORD, FIRST_NAME, LAST_NAME, BASE_URL
    )


## initialize client


.. code-block:: python

    client = BESClient(
        email=EMAIL,
        password=PASSWORD,
        organization_token=ORG_TOKEN,
        base_url=BASE_URL
    )


## get resource type mapping


.. code-block:: python

    resource_types = get_resource_type(client)



## Create a preview building


.. code-block:: python

    preview_building_1 = client.create_preview_building(
        assessment_type='Test',
        building_name='Preview Example 1',
        year_completed='1990',
        floor_area='100000',
        street='123 Street',
        city='Boring',
        state='OR',
        postal_code='97009',
        use_type='Office',
        number_floors=5,
        orientation='North/South'
    )


## get the building details


.. code-block:: python

    building_id_1 = preview_building_1['building_id']
    building_details_1 = client.get_preview_building(building_id_1)


Building details 1::

    {u'address': u'123 Street',
     u'assessment_type': u'Test',
     u'blocks': [{u'block_id': 257,
       u'floor:floor_type': u'Slab-on-Grade',
       u'floor:floor_type_status!': u'Do not know',
       u'hvac_system:type': u'VAV with Hot-Water Reheat',
       u'hvac_system:type_status!': u'Do not know',
       u'lighting': [{u'fixture_status!': u'Do not know',
         u'id': 402,
         u'lamp_type': u'Fluorescent T12',
         u'mounting_type': u'Recessed',
         u'percent_served': 90.0,
         u'percent_served_status!': u'Do not know'},
        {u'fixture_status!': u'Do not know',
         u'id': 403,
         u'lamp_type': u'Incandescent/Halogen',
         u'mounting_type': u'Recessed',
         u'percent_served': 10.0,
         u'percent_served_status!': u'Do not know'}],
       u'roof:roof_type': u'Built-up w/ metal deck',
       u'roof:roof_type_status!': u'Do not know',
       u'surfaces:window_wall_ratio': u'0.36',
       u'surfaces:window_wall_ratio_status!': u'Do not know',
       u'use_type:name!': u'Office',
       u'wall:wall_type': u'Brick/Stone on masonry',
       u'wall:wall_type_status!': u'Do not know',
       u'water_heater:fuel_type': u'Natural Gas',
       u'water_heater:fuel_type_status!': u'Do not know',
       u'window:framing_type': u'Metal w/ Thermal Breaks',
       u'window:framing_type_status!': u'Do not know',
       u'window:glass_type': u'Double Pane',
       u'window:glass_type_status!': u'Do not know'}],
     u'building_id': 334,
     u'city': u'Boring',
     u'name': u'Preview Example 1',
     u'notes': u'Built via V2 API',
     u'orientation!': u'North/South',
     u'state': u'OR',
     u'status!': u'Editing',
     u'total_floor_area!': 100000.0,
     u'year_of_construction': 1990,
     u'zip_code': u'97009'}


##  Update some details
### Update the water heater

This uses some v1 api calls.


.. code-block:: python

    block_1 = building_details_1['blocks'][0]

    fuel_types = resource_types['fuel_types']

    resources = client.get_block_resources('water_heater', block_1['block_id'])
    water_heater_id = resources[0]['water_heater_id']

    # not needed for update but allows you to see what can be set
    water_heater = client.get_resource('water_heater', water_heater_id)

    client.update_resource(
        'water_heater',
        water_heater_id,
        tank_insulation_r_value=11
      )

    client.update_resource(
        'water_heater',
        water_heater_id,
        fuel_type_id=fuel_types['electricity']['id']
    )


### set mode to editing


.. code-block:: python

    client.set_preview_building_status(building_id_1, 'edit_mode')



### update the floor type

The value for floor type is one of ``resource_types['floot_types'].keys()``

.. code-block:: python

    client.update_preview_building(
        building_id_1,
        block_1['block_id'],
        extras={'floor:floor_type': 'wood framed'}
    )


## Validate the building and run simulation

.. code-block:: python

    result = client.validate_preview_building(building_id_1)
    if result == 'valid':
      client.simulate_preview_building(building_id_1)


**Note simulating the building may take some time.**

### Get some details

.. code-block:: python

    status = client.get_preview_building(building_id_1)['status!']
    if status == 'Rated':
        details = client.get_preview_building(building_id, report_type='pdf')

details::

    {
        u'name': u'Preview Example 1',
        u'id': 344
        u'pdf_url': u'http://api.labworks.org/buildings/344/report.pdf',
        u'potential_energy_savings': 30,
        u'low_score': 3.5,
        u'potential_low_score': 6.0,
        u'high_score': 7.5,
        u'potential_high_score': 10.0,
        u'mean_eui': 158.85740661621094,
        u'min_eui': 88.42064666748047,
        u'max_eui': 250.76022338867188,
    }


Contributing
------------

License
-------
py-bes is released under the terms of the MIT license. Full details in LICENSE file.

Changelog
---------
For a full changelog see `CHANGELOG.rst <https://github.com/GreenBuildingRegistry/py-bes/blob/master/CHANGELOG.rst>`_.