import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import StringIO
from shapely.geometry import Point

from typing import Optional

import censusdis.data as ced
import censusdis.maps as cem
import censusdis.values as cev
from censusdis import states

CENSUS_VARS = {
    "NAME" : "NAME",
    "B19013_001E" : "median_hh_income",
    "B01001_001E" : "total_pop",
    "B17001_002E" : "pop_in_poverty",
    "B03002_003E" : "white_pop",
    "B03002_004E" : "black_pop",
    "B03002_006E" : "asian_pop",
    "B03002_012E" : "hispanic_pop",
    "B03002_005E" : "native_american_pop",
    "B03002_009E" : "two_or_more_pop",
    "B25003_001E" : "total_households",
    "B25003_002E" : "owner_households",
    "B25003_003E" : "renter_households",
    "B25077_001E" : "median_home_value",
    "B25002_001E" : "total_housing_units",
    "B25002_003E" : "vacant_units"
}

print("Retrieving data from census api")
US_block_groups = ced.download("acs/acs5",
                2021,
                CENSUS_VARS,
                state=states.ALL_STATES,
                county = "*",
                tract = "*",
                block_group = "*",
                with_geometry=True
                ).rename(CENSUS_VARS, axis = 1)

US_block_groups["GEOID"] = US_block_groups["STATE"] + US_block_groups["COUNTY"] + US_block_groups["TRACT"] + US_block_groups["BLOCK_GROUP"]

US_block_groups.to_file("data/processed/US_bg_census.geojson")