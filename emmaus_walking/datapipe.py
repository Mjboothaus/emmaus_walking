# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_datapipe.ipynb (unless otherwise specified).

__all__ = ['calc_walk_stats', 'load_and_cache_raw_walk_data']

# Internal Cell
import os
import pandas as pd
import activityio as aio
from dateutil.parser import parse
import datetime as dt

# Cell
def calc_walk_stats(walk_data):
    total_time = dt.timedelta(0)
    total_distance = 0

    for iHike, hike in enumerate(walk_data):
        total_time += hike.index.max()
        # print(iHike+1, walk_date[iHike], hike.index.max(), hike['dist'].max() / 1e3)
        total_distance += hike['dist'].max()
    total_distance /= 1e3

    start_coord = walk_data[0][['lat', 'lon']].iloc[0].tolist()
    end_coord = walk_data[-1][['lat', 'lon']].iloc[-1].tolist()
    return total_time, total_distance, start_coord, end_coord


# TODO: use st.cache() and also look to pre-load and cache/feather data (or similar) - NB: use of @st.cache() below didn't work
def load_and_cache_raw_walk_data(walk_name, sample_freq):
    FIT_FILE_PATH = '/Users/mjboothaus/iCloud/Data/HealthFit/'
    data_dir = FIT_FILE_PATH + walk_name[0:3] + '/'
    data_files = [file for file in os.listdir(data_dir) if file.endswith('.fit')]
    walk_files = sorted(data_files)

    walk_data = []
    walk_date = []

    for iFile, file in enumerate(walk_files):
        walk_data.append(pd.DataFrame(aio.read(data_dir + file)))
        walk_date.append(parse(file[0:17]))

    total_time, total_distance, start_coord, end_coord = calc_walk_stats(walk_data)
    walk_merged = pd.concat(walk_data)
    points = walk_merged[['lat', 'lon']].values.tolist()
    points = [tuple(point) for ipoint, point in enumerate(points) if ipoint % sample_freq == 0]
    return walk_data, walk_date, walk_files, points