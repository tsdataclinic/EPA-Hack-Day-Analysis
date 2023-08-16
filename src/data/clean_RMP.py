import numpy as np
import pandas as pd
import os
import geopandas as gpd
from shapely.geometry import Point
from io import StringIO
import matplotlib.pyplot as plt

from censusdis import data as ced

# Load data
RMP_facilities = pd.read_csv("data/processed/facilities_trimmed.csv")
naics = pd.read_csv("data/raw/naics-codes.csv")

# Most recent submissions
RMP_submissions = pd.read_csv("data/raw/submissions.csv")
RMP_submissions_trimmed = RMP_submissions[['EPAFacilityID', 'FacLat', 'FacLng','ReceiptDate']].sort_values(['ReceiptDate'],ascending=True).groupby('EPAFacilityID').tail(1)
RMP_facilities = RMP_facilities.join(RMP_submissions_trimmed.set_index('EPAFacilityID'), on='EPAFacilityID')

# Fill in missing coords
RMP_facilities['Lat'] = RMP_facilities['Lat'].fillna(RMP_facilities['FacLat'])
RMP_facilities['Lng'] = RMP_facilities['Lng'].fillna(RMP_facilities['FacLng'])

# Industry codes
RMP_facilities["NAICS_3"] = RMP_facilities["NAICSCode"].astype(str).str.slice(0,3)
RMP_facilities["NAICS_2"] = RMP_facilities["NAICSCode"].astype(str).str.slice(0,2)

RMP_facilities = RMP_facilities.merge(naics.rename({"NAICSCode" : "NAICS_3", "Description" : "Description_3"}, axis =1), how = "inner")
RMP_facilities = RMP_facilities.merge(naics.rename({"NAICSCode" : "NAICS_2", "Description" : "Description_2"}, axis =1), how = "inner")

# Drop remaining missing coords
RMP_facilities = RMP_facilities.drop(["FacLat", "FacLng"], axis = 1)

RMP_facilities = RMP_facilities.dropna(subset=["Lat","Lng"])
RMP_facilities["geometry"] = [Point(x, y) for x, y in zip(RMP_facilities.Lng, RMP_facilities.Lat)]
RMP_facilities = gpd.GeoDataFrame(RMP_facilities, geometry='geometry', crs ="EPSG:4326")

# Identify counties

DATASET = "acs/acs5"
YEAR = 2020
CENSUS_VARS = {"NAME" : "NAME",
}

counties = ced.download(
            DATASET,
            YEAR,
            CENSUS_VARS,
            state="*",
            county = "*",
            with_geometry=True
            ).to_crs(4326)

counties["county_geoid"] = counties["STATE"] + counties["COUNTY"]

counties["county_name"] = counties["NAME"]

RMP_facilities.overlay(counties[["county_geoid", "county_name", "geometry"]].to_crs(4326))

# Save
RMP_facilities.to_file("data/processed/facilities_geo.geojson")