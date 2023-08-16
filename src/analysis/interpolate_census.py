import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import StringIO
from shapely.geometry import Point

from typing import Optional
from shapely.ops import unary_union

import numpy as np

pd.options.mode.chained_assignment = None

DATA_DIR = "data/cache_interpolated/"

print(os.getcwd())

from src.utils.areal_interpolation import (
    interpolate_multiple_buffers_advanced,
    compute_proportions
)


gdf_tract = gpd.read_file("data/processed/US_bg_census.geojson").to_crs(2263)
gdf_urban_all = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER_RD18/LAYER/UAC20/tl_rd22_us_uac20.zip").rename(columns = {"NAME20": "UA_NAME"}).to_crs(2263)
RMP_facilities = gpd.read_file("data/processed/facilities_geo.geojson").to_crs(2263)

# Process names
gdf_urban_all["UACE"] = gdf_urban_all["UACE20"]
name_uace_map = {
    x['UA_NAME'] : x['UACE']
    for _,x in gdf_urban_all.iterrows()
}
gdf_urban_all["UACE"] =  gdf_urban_all["UACE"].astype("int")

# Columns to interpolate
sum_columns = ["total_pop", "white_pop", "hispanic_pop", "black_pop",'total_households','renter_households','total_housing_units','vacant_units']
mean_dict = {'total_households' : 'median_hh_income', 'total_housing_units' : 'median_home_value'}
prop_dict =  {"total_pop":["white_pop", 'hispanic_pop', "black_pop"], "total_households": 'renter_households', "total_housing_units": 'vacant_units'}

# Urban area stats
urban_stats = interpolate_multiple_buffers_advanced(
    census_data = gdf_tract,
    facilities = gdf_urban_all,
    buffer_miles_list = [0], 
    census_vars_sum = sum_columns, 
    census_vars_mean = mean_dict, 
    file_dir = DATA_DIR, facility_index_name = 'UACE'
)
compute_proportions(urban_stats, prop_dict, [0])

# Create fenceline polygons
facility_tract_overlap = RMP_facilities.sjoin(gdf_urban_all[['UACE','UA_NAME','geometry']],how='left',predicate='intersects').dropna(subset=['UACE']).drop(['index_right'], axis = 1)
facility_tract_overlap['buffer_geometry'] = facility_tract_overlap["geometry"].buffer(1 * 5280, cap_style = 1)
facility_tract_overlap.set_geometry("buffer_geometry", inplace=True)
fenceline = gdf_urban_all[['UACE','UA_NAME','geometry']].rename(columns = {'geometry':"UA_geometry"}).set_geometry("UA_geometry").join(
    gpd.GeoDataFrame(facility_tract_overlap.groupby("UACE")['buffer_geometry'].apply(lambda x: unary_union(x)).rename("buffer_facility")), on = 'UACE'
).dropna().join(facility_tract_overlap.groupby(['UACE'])['EPAFacilityID'].count().rename("facility_count"), on='UACE')
fenceline['geometry'] = fenceline['UA_geometry'].intersection(fenceline['buffer_facility'].set_crs(epsg=2263))

# Fenceline stats 
fenceline_stats = interpolate_multiple_buffers_advanced(
    census_data = gdf_tract,
    facilities = fenceline,
    buffer_miles_list = [0], 
    census_vars_sum = sum_columns, 
    census_vars_mean = mean_dict,
    file_dir = DATA_DIR,
    facility_index_name = 'UACE', file_name = 'all.csv'
)
compute_proportions(fenceline_stats, prop_dict, [0])

# Process ratios
df = fenceline.drop(['geometry'],axis = 1).merge(fenceline_stats, on='UACE').merge(
    urban_stats, on='UACE', suffixes = ("_fenceline", "_urban")
)

ratio_cols = ['white_pop', 'black_pop', 'hispanic_pop','renter_households','vacant_units','median_hh_income','median_home_value']

for x in ratio_cols[0:5]:
    df[x + "_ratio"] = df[x + "_buffer_0_proportion_fenceline"] / df[x + "_buffer_0_proportion_urban"]
for x in ratio_cols[5:]:
    df[x + "_ratio"] = df[x + "_buffer_0_fenceline"] / df[x + "_buffer_0_urban"]

df_stats = df[['UACE', 'UA_NAME', 'facility_count'] + [x + "_ratio" for x in ratio_cols]]

# Out
df_stats.to_csv("data/processed/urban_area_statistics.csv")