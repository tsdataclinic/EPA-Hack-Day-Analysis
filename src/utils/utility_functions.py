from io import StringIO
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import censusdis.data as ced


def national_bg(var_dictionairy):
    """
    Takes list of variables and queries 2020 acs for all 50 states
    """
    
    DATASET = "acs/acs5"
    YEAR = 2020
    states = [str(i).zfill(2) for i in range(1, 57)]

    US_tracts = gpd.GeoDataFrame()
    for state in states:
        if state not in ["03", "07", "14", "43", "52"]: 
            tract_temp = ced.download(
                DATASET,
                YEAR,
                var_dictionairy,
                state=state,
                county = "*",
                tract = "*",
                block_group = "*",
                with_geometry=True
                ).rename(var_dictionairy, axis = 1)
            US_tracts = pd.concat([US_tracts, tract_temp])
    return US_tracts
