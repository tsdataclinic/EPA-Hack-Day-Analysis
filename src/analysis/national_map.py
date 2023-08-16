import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import StringIO
from shapely.geometry import Point

import pickle
import numpy as np

RMP_data = gpd.read_file("data/processed/facilities_geo.geojson")
gdf_urban_all = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER_RD18/LAYER/UAC20/tl_rd22_us_uac20.zip").rename(columns = {"NAME20": "UA_NAME"})[['UA_NAME','geometry']]
UA_stats = pd.read_csv("data/processed/urban_area_statistics.csv").query("facility_count >= 10")

gdf_urban_all = gdf_urban_all.merge(UA_stats["UA_NAME"])
RMP_UA = RMP_data.overlay(gdf_urban_all.to_crs(4326))

RMP_UA["description"] = "Urban Area: " + RMP_UA["UA_NAME"] + "<br>" + "City/Town: " + RMP_UA["City"] + '<br>' + "Facility Industry: " + RMP_UA["Description"]

gdf_urban_all["geometry"] = gdf_urban_all.simplify(0.001)

gdf_urban_all[["UA_NAME", "geometry"]].to_file("viz/viz_data/urban_areas.geojson")
RMP_UA[["EPAFacilityID", "description", "geometry"]].to_file("viz/viz_data/RMP_facilities.geojson")