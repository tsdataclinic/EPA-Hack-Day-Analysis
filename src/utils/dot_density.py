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

def get_rmp_zones(UA_tracts, RMP_facilities, buffer_miles):
    UA_facilities = RMP_facilities.overlay(UA_tracts, keep_geom_type=False)
    UA_facilities = UA_facilities.set_geometry(UA_facilities.buffer(5280 * buffer_miles))
    
    geo = unary_union(UA_facilities.geometry)

    return(gpd.GeoDataFrame(geometry = [geo], crs = "epsg:2263"))

def read_water_file(url):
    # Accesses and reads water file from url
    session = requests.Session()
    response = session.get(url)
    assert response.status_code == 200

    zipfile_io = io.BytesIO(response.content)

    zip = zipfile.ZipFile(zipfile_io)
    zip.extractall("water_tmp")

    for file in os.listdir("water_tmp"):
        if file.endswith('.shp'):
            shapefile_name = file
            break
    
    gdf = gpd.read_file("water_tmp/" + shapefile_name)

    for file in os.listdir("water_tmp"):
        os.remove("water_tmp/" + file)
    os.rmdir("water_tmp")
    
    return(gdf)

def get_water(UA_tracts, threshold = 10000):
    # Downloads and concatenates water files
    distinct_counties = UA_tracts.GEOID.str.slice(0,5).unique()
    gdfs = []

    for county in distinct_counties:
        url = "https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_" + county + "_areawater.zip"
        temp_gdf = read_water_file(url)
        gdfs.append(temp_gdf) 
    
    gdf = gpd.GeoDataFrame(pd.concat(gdfs))
    gdf = gdf.set_geometry("geometry").to_crs(2263)

    if threshold:
        gdf = gdf.query("AWATER > @threshold")

    return gdf

def remove_water_from_tracts(UA_tracts):
    # Drops water from tract geometry
    water = get_water(UA_tracts)
    unified_water = water.geometry.unary_union
    UA_geom_without_water = UA_tracts.geometry.apply(lambda tract: tract.difference(unified_water))

    return UA_tracts.set_geometry(UA_geom_without_water)

def get_UA_tracts(urban_area_name: str, tracts: gpd.GeoDataFrame, UA_geo: gpd.GeoDataFrame, areal_weight_columns: list):
    # Intersects census tracts with urban area geometry. Recalculates using weights where overlap is incomplete.
    tracts["area"] = tracts.area
    UA = UA_geo.query("UA_NAME == @urban_area_name")
    UA_tracts = UA.overlay(tracts, how="intersection", keep_geom_type=False)
    UA_tracts = remove_water_from_tracts(UA_tracts)
    UA_tracts["UA_area"] = UA_tracts.area
    UA_tracts["areal_weight"] = UA_tracts["UA_area"] / UA_tracts["area"]
    UA_tracts[areal_weight_columns] = round(UA_tracts[areal_weight_columns].apply(lambda x: x*UA_tracts["areal_weight"]))
    UA_tracts = UA_tracts.query("total_pop > 50")
    UA_tracts = UA_tracts[UA_tracts.area > 0]
    return UA_tracts.reset_index()

def calculate_prop_vectors(city_tracts, numerator_cols: list, denominator_col: str):
    prop_cols = city_tracts[numerator_cols].apply(lambda x: x/city_tracts[denominator_col])

    prop_cols["other"] = np.max(1 - prop_cols.sum(axis=1), 0)
    row_totals = prop_cols.sum(axis=1)
    prop_cols = prop_cols.divide(row_totals, axis=0)
    
    prop_df = pd.DataFrame({"GEOID": city_tracts["GEOID"], "pdf": prop_cols.apply(lambda x: x.to_list(), axis=1)})
    return prop_df
def bb_area(x1, y1, x2, y2):
    return (x2 - x1) * (y2 - y1)

# https://www.matecdev.com/posts/random-points-in-polygon.html
def gen_random_points_in_bb(polygon: Polygon, num: int):
    minx, miny, maxx, maxy = polygon.bounds
    # print(polygon.bounds)
    return [Point(element) for element in list(zip(np.random.uniform( minx, maxx, num ), np.random.uniform( miny, maxy, num )))]

def gen_random_points_in_poly(polygon: Polygon, num: int, GEOID: str):
    area = polygon.area
    # print(polygon.bounds)
    _bb_area = bb_area(*polygon.bounds)
    # mul by 1.5 to make that most of the time, enough points land inside the geometry
    num_in_bb = int(1.5 * num * (_bb_area / area))
    bb_points = gen_random_points_in_bb(polygon, num_in_bb)

    points_list = list(filter(lambda point: polygon.contains(point), bb_points))[:num]
    points_gdf = gpd.GeoDataFrame(geometry = points_list)
    points_gdf["GEOID"] = GEOID
    return points_gdf

def create_points_for_city(city_tracts, pop_per_point):
    # Slightly awkward iteration bc I was having trouble getting apply to do what I wanted
    gdfs = []
    for i in range(len(city_tracts.index)):
        points_per = int(city_tracts["total_pop"][i] // pop_per_point)
        temp_gdf = gen_random_points_in_poly(city_tracts["geometry"][i], points_per, city_tracts["GEOID"][i])
        gdfs.append(temp_gdf)

    gdf = gpd.GeoDataFrame(pd.concat(gdfs))
    return gdf

def gen_dot_density(polygon:Polygon, total_pop:int, pop_per_point:int, pdf: np.array, labels: list):
    points = gen_random_points_in_poly(polygon, int(total_pop // pop_per_point))
    return [
        {
            "ethnicity": np.random.choice(labels, p=pdf),
        "x": point.x,
        "y": point.y} for point in points]

def augment_points_with_labels(points: gpd.GeoDataFrame, prop_df: pd.DataFrame, name: str, labels: list):

    points_prop = points.merge(prop_df)
    points_prop[name] = points_prop.apply(lambda row: np.random.choice(labels, p=row["pdf"]), axis = 1)
    points_prop = points_prop.drop("pdf", axis = 1)
    
    return points_prop

def get_ppp(pop):
    if pop < 500000:
        return 25
    elif pop < 1000000:
        return 50
    elif pop < 2000000:
        return 100
    else:
        return 150