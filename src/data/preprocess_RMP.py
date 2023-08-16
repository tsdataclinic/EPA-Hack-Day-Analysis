from typing import Optional
import pandas as pd
from io import StringIO
from datetime import datetime


# Facilities are required to submit and RMP every 5 years 
# We remove facilities that don't have a submission after 2017
facilities = pd.read_csv("data/raw/facilities.csv")
facilities = facilities[facilities.LatestDeregDate.isna()]


# List of chemicals used by each facility
facilities["chemicals_used"] = facilities.ChemicalsInLatest.str.split(" • ")
facility_chemicals = facilities.explode("chemicals_used")[["EPAFacilityID", "chemicals_used"]]

# Industry codes
naics = pd.read_csv("data/raw/naics-codes.csv")
facilities.NAICSCodesInLatest.head(50)
facilities["NAICSCode"] = facilities.NAICSCodesInLatest.str.split(" • ")
facility_naics = facilities.explode("NAICSCode")[["EPAFacilityID", "NAICSCode"]].merge(naics)
first_naics = facility_naics.drop_duplicates("EPAFacilityID")

# Columns of interest
facility_cols = ["EPAFacilityID", "LatestCompany1", "City", "State", "Lat", "Lng", "NumSubmissions", "NumAccidentsInLatest"]
facilities_trim = facilities.copy()[facility_cols]
facilities_trim.loc[:, "any_accidents"] = facilities_trim["NumAccidentsInLatest"] > 0
facilities_trim = facilities_trim.merge(first_naics)

# Out
facilities_trim.to_csv("data/processed/facilities_trimmed.csv")
facility_chemicals.to_csv("data/processed/facility_chemicals.csv")
facility_naics.to_csv("data/processed/facility_naics.csv")