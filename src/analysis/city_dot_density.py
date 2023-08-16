import geopandas as gpd
import pandas as pd
import os
import zipfile
import io
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import pathlib
import requests
import numpy as np

from src.utils.dot_density import *

gdf_urban_all = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER_RD18/LAYER/UAC20/tl_rd22_us_uac20.zip").rename(columns = {"NAME20": "UA_NAME"})[['UA_NAME','geometry']].to_crs(2263)
gdf_tract = gpd.read_file("data/processed/US_bg_census.geojson").to_crs(2263)
RMP_facilities = gpd.read_file("data/processed/facilities_geo.geojson").to_crs(2263)
UA_stats = pd.read_csv("data/processed/urban_area_statistics.csv").query("facility_count >= 10")

AREAL_WEIGHT_COLUMNS = ["total_pop", "pop_in_poverty", "white_pop", 'black_pop', 'asian_pop',
       'hispanic_pop', 'native_american_pop', 'two_or_more_pop',
       'total_households', 'owner_households', 'renter_households']

from dataclasses import dataclass
from geopandas.geodataframe import GeoDataFrame

@dataclass
class DotDensityConfiguration:
    city_name: str
    ppp: int
    output_dir_prefix: str
    crs: int
    
@dataclass
class DotDensityRenderOutput:
    config: DotDensityConfiguration
    rmp_buffers: GeoDataFrame
    dot_density: GeoDataFrame
    ppp: int

def render_city_data(config: DotDensityConfiguration) -> DotDensityRenderOutput:
    city = get_UA_tracts(config.city_name, gdf_tract, gdf_urban_all, areal_weight_columns = AREAL_WEIGHT_COLUMNS)
    city_points = create_points_for_city(city, config.ppp)
    city_race_props = calculate_prop_vectors(city, ["white_pop", "black_pop", "asian_pop", "hispanic_pop"], "total_pop")
    labels= ["White", "Black", "Asian", "Hispanic/Latino", "Another race"]
    race_points = augment_points_with_labels(city_points, city_race_props, "race", labels)
    rmp_buffers = get_rmp_zones(city, RMP_facilities, 1)
    race_points = race_points.set_geometry("geometry").set_crs(2263)
    
    return DotDensityRenderOutput(
        config=config,
        rmp_buffers=rmp_buffers.to_crs(config.crs),
        dot_density=race_points.to_crs(config.crs),
        ppp=config.ppp)

def export_viz_to_json_data(path: pathlib.Path, render_output: DotDensityRenderOutput):
    full_path = path / render_output.config.output_dir_prefix
    print(full_path)
    full_path.mkdir(parents=True, exist_ok=True)
    render_output.rmp_buffers.to_file(str(full_path / "rmp_buffers.geojson"), DRIVER="json")
    render_output.dot_density.to_file(str(full_path / "dot_density.geojson"), DRIVER="json")
    pd.DataFrame([render_output.ppp], columns = ["ppp"]).to_csv(str(full_path / "ppp.csv"))

list_of_cities = UA_stats.UA_NAME.unique()

def process_name(city):
    city = city.split(',')[0]
    return ''.join(letter for letter in city if letter.isalpha()).lower()

for city in list_of_cities:
        prefix = process_name(city)
        city_pop = get_UA_tracts(city, gdf_tract, gdf_urban_all, areal_weight_columns=AREAL_WEIGHT_COLUMNS).total_pop.sum()
        ppp = get_ppp(city_pop)
        print(city)
        config = DotDensityConfiguration(city_name=city, ppp=ppp, output_dir_prefix=prefix, crs=4326)
        result = render_city_data(config)
        export_viz_to_json_data(pathlib.Path("data/viz/"), result)