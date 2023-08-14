from io import StringIO
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import censusdis.data as ced

def buffered_str(x, buffer_miles = None):
    if buffer_miles is None:
        return x
    else: 
        return x + "_buffer_" + str(buffer_miles)

def make_list(v):
    return v if isinstance(v, list) else [v]

def weighted_average_skipnan(df, weight_col, data_col, by_cols = None):
    '''
        Taken from https://stackoverflow.com/a/44683506
    '''
    df['_data_times_weight'] = df[data_col] * df[weight_col]
    df['_weight_where_notnull'] = df[weight_col] * pd.notnull(df[data_col])
    if by_cols: 
        g = df.groupby(by_cols)
        result = g['_data_times_weight'].sum() / g['_weight_where_notnull'].sum()
    else: 
        result = df['_data_times_weight'].sum() / df['_weight_where_notnull'].sum()
    del df['_data_times_weight'], df['_weight_where_notnull']
    return result

def interpolate_tracts_buffer_advanced(
    census_data, facilities, buffer_miles, census_vars_sum, census_vars_mean, index_name, file_dir = None, file_name = None
):
    """
    Creates interpolated estimates from a list of buffers. 
    All columns in census_vars_sum are estimated using area weights.
    census_vars_mean specifies weights to use for each column, e.g. 
        census_vars_mean = {
            'total_pop_over_16': ['median_age', 'median_income']
            'total_households' : 'median_hh_income', 
            'total_housing_units' : 'median_home_value'
        }
    """
    
    import os.path
    
    rmp_tract_overlay = None
    if file_name is None:
        file_name = f"{buffer_miles}mile.csv"
    if (file_dir and os.path.exists(file_dir + file_name)):
        rmp_tract_overlay = pd.read_csv(file_dir + file_name,usecols=[index_name,'NAME','tract_overlap_prop']).merge(census_data, on="NAME").merge(facilities, on=index_name)
        print("Overlaying geometries were previously computed!")
    else: 
        ### 2263 is in ft units, and 1 mile = 5280 ft
        buffer = buffer_miles * 5280

        census_data = census_data.to_crs("epsg:2263")
        census_data["tract_area"] = census_data.area

        facilities = facilities.to_crs("epsg:2263")
        facilities["buffer_geometry"] = facilities["geometry"].to_crs("EPSG:2263")
        if (buffer > 0.):
            facilities["buffer_geometry"] = facilities["buffer_geometry"].buffer(buffer, cap_style = 1)
        facilities.set_geometry("buffer_geometry", inplace=True)
        facilities["buffer_area"] = facilities.area
        print("Data cleaned!")

        rmp_tract_overlay = facilities.overlay(census_data, how='intersection', keep_geom_type=False)
        rmp_tract_overlay["intersection_area"] = rmp_tract_overlay.area
        rmp_tract_overlay['tract_overlap_prop'] = rmp_tract_overlay['intersection_area'] / rmp_tract_overlay['tract_area']
        print("Geometries overlaid!")
        if file_dir:
            rmp_tract_overlay[[index_name,'NAME','STATE','COUNTY','TRACT','tract_overlap_prop','intersection_area']].to_csv(
                file_dir + file_name,index=False
            )
    
    for variable in set(census_vars_sum).union(census_vars_mean.keys()):
        rmp_tract_overlay[buffered_str(variable, buffer_miles)] = rmp_tract_overlay[variable] * rmp_tract_overlay['tract_overlap_prop']
    print("Finished computing sums!")
    rmp_facility_buffer_sum_estimates = (
        rmp_tract_overlay[[index_name] + [buffered_str(variable, buffer_miles) for variable in census_vars_sum]]
        .groupby([index_name])
        .sum()
    )
    
    if census_vars_mean:
        for k, v in census_vars_mean.items(): 
            for variable in make_list(v): 
                rmp_facility_buffer_sum_estimates = rmp_facility_buffer_sum_estimates.join(
                    weighted_average_skipnan(rmp_tract_overlay, buffered_str(k, buffer_miles), variable, index_name)
                    .rename(buffered_str(variable, buffer_miles)),
                )
        print("Finished computing means!")

    return rmp_facility_buffer_sum_estimates.reset_index()

def interpolate_multiple_buffers_advanced(census_data, facilities, buffer_miles_list, file_dir, census_vars_sum, census_vars_mean = {}, facility_index_name = 'EPAFacilityID', file_name = None):
    """
    Wrapper for interpolating multiple buffers and joining results
    """
    
    out = pd.DataFrame()
    for buffer_miles in buffer_miles_list:
        print(f"=== Computing {buffer_miles} radius ===")
        temp = interpolate_tracts_buffer_advanced(census_data, facilities, buffer_miles, census_vars_sum, census_vars_mean, facility_index_name, file_dir, file_name)
        if out.shape == (0,0):
            out = temp
        else: 
            out = out.merge(temp, on = index_name)
    return out

def compute_proportions(df, cols, buffer_miles_list=None):
    for total_col, subset_cols in cols.items(): 
        for variable in make_list(subset_cols):
            for buffer_miles in make_list(buffer_miles_list): 
                df[buffered_str(variable, buffer_miles) + "_proportion"] = df[buffered_str(variable, buffer_miles)] / df[buffered_str(total_col, buffer_miles)]