# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/88_app.ipynb (unless otherwise specified).

__all__ = ['DATA_INFO', 'AUTHOR_INFO', 'APP_NAME', 'CACHED_WALK_DATA', 'plot_walk', 'plot_entire_walk',
           'plot_walk_points', 'SideBar', 'app_sidebar', 'IMAGE_PATH', 'IMAGE_PATH', 'WALK_NAME', 'WALK_NAME',
           'load_cached_walking_data', 'app_mainscreen', 'notebook_mainscreen', 'sb']

# Cell

import numpy as np
import pandas as pd
import datetime as dt
from pathlib import Path
import streamlit as st
from streamlit_folium import folium_static
import folium
from PIL import Image
from IPython.display import display
#import os, io
#import activityio as aio
#from dateutil.parser import parse

# Cell
# TODO: Following is a hack to fix issue with import paths using nbdev in notebook vs. app
try:
    from .core import in_notebook
    from .datapipe import load_and_cache_raw_walk_data, calc_walk_stats
except:
    from core import in_notebook
    from datapipe import load_and_cache_raw_walk_data, calc_walk_stats

# Cell

DATA_INFO = 'Apple Watch via Health Fit'
AUTHOR_INFO = 'by [DataBooth.com.au](https://www.databooth.com.au)'
APP_NAME = 'Emmaus Walking Mapping App'
CACHED_WALK_DATA = 'emmaus_walking.cache.feather'

st.set_page_config(page_title=APP_NAME, layout='wide')

# Cell

def plot_walk(walk_df, map_handle, linecolour, linewidth, freq=100):
    points = []
    count = 0
    for index, row in walk_df.iterrows():
        count+=1
        if count%freq == 0:
            points.append((row['lat'], row['lon']))
    folium.PolyLine(points, color=linecolour, weight=linewidth).add_to(map_handle)


def plot_entire_walk(walk_data, map_handle, linecolour, linewidth):
    for iHike, hike in enumerate(walk_data):
        plot_walk(hike, map_handle, linecolour, linewidth)


def plot_walk_points(walk_points, map_handle, linecolour, linewidth):
    folium.PolyLine(walk_points, color=linecolour, weight=linewidth).add_to(map_handle)

# Cell

IMAGE_PATH = 'emmaus_walking/resources'
IMAGE_PATH = Path.cwd().resolve()/IMAGE_PATH

WALK_NAME = ['B2M: Bondi to Manly', 'B2W: Bondi to Wollongong', 'D2C: Drummoyne to Cockatoo', 'GNW: Great North Walk', \
            'GTL: Gladesville Loop', 'GWW*: Great West Walk', 'OLD: Old Bar', "STM: St Michael's Golf Course", \
            'WNG*: Newcastle to Sydney']  # TODO: Extract this info from the cached meta-data file - from the meta-data in the database

WALK_NAME = WALK_NAME + ['ALL: All Walks']

class SideBar:
    datasource = DATA_INFO
    datasize = 0   # look to calculate this (in MB?) - TEST: Comment change
    author = AUTHOR_INFO
    data_title = 'Data details...'
    data_local = False
    start_date = dt.date.today()
    end_date = dt.date.today()
    selected_data = None
    walk_name = ''
    linewidth = 4
    linecolour = 'blue'
    show_individual_walks = False


def app_sidebar(APP_NAME):

    sb = SideBar()

    st.sidebar.info(APP_NAME)

    col1, col2 = st.sidebar.beta_columns(2)

    with col1:
        image1 = Image.open(IMAGE_PATH/'AppleWatchExercise.jpeg').resize((144, 144))  # NOTE: resize done here
        st.image(image=image1, use_column_width=True, output_format='JPEG')
    with col2:
        image2 = Image.open(IMAGE_PATH/'HealthFitLogo.png')
        st.image(image=image2, use_column_width=True, output_format='PNG')

    st.sidebar.markdown(sb.author)
    #st.sidebar.markdown(sb.datasource)
    #st.sidebar.info(sb.data_title)
    #st.sidebar.markdown('Datasize: ' + str(sb.datasize))
    sb.walk_name = st.sidebar.selectbox('Choose a walk [* indicates still in progress]', WALK_NAME, 0)
    sb.linewidth = st.sidebar.slider('Line width:', min_value=1, max_value=5, value=3)
    sb.linecolour = st.sidebar.radio('Line colour:', ['blue', 'green', 'red', 'yellow'], 0)
    sb.show_individual_walks = st.sidebar.checkbox('Show individual walks', value=False, key=None, help=None)

    return sb

# Cell

@st.cache
def load_cached_walking_data():
    all_walks_df = pd.read_feather(CACHED_WALK_DATA)   # load cached (downsampled) data
    return all_walks_df

# Cell

def app_mainscreen(APP_NAME, sb):

    #st.title(APP_NAME)
    st.header(sb.walk_name)

    # Load walking data
    # OLD_WAY ---------------------------------------------------------------------------------------------
    # sample_freq=50
    # walk_data, walk_date, walk_files, walk_points = load_and_cache_raw_walk_data(sb.walk_name, sample_freq)

    walk_name = sb.walk_name[0:3]
    all_walks_df = load_cached_walking_data()

    if walk_name != 'ALL':
        walk_points = all_walks_df[all_walks_df['WalkName']==walk_name].groupby('WalkNumber')[['lat', 'lon']]
    else:
        walk_points_all = []
        for wname in all_walks_df['WalkName'].unique():
            walk_points = all_walks_df[all_walks_df['WalkName']==wname].groupby('WalkNumber')[['lat', 'lon']]
            walk_points_all.append(walk_points)

    sb.datasize = all_walks_df.memory_usage(deep=True).sum() / 1024 / 1024

    walk_data = []
    for _, group in walk_points:
        walk_data.append(group[['lat', 'lon']].values.tolist())

    # walk_points = all_walks_df[all_walks_df['WalkName']==walk_name][['lat', 'lon']].values.tolist()

    # TODO: Need to plot sub-walks seperately to avoid ordering issues

    # total_time, total_distance, start_coord, end_coord = calc_walk_stats(walk_data)

    start_coord = (0, 0)

    map_handle = folium.Map(start_coord, zoom_start=13, detect_retina=True, control_scale=True)

    # plot_walk_points(walk_points, map_handle, sb.linecolour, sb.linewidth)

    if walk_name != 'ALL':
        for nwalk, walk in enumerate(walk_data):
            if sb.show_individual_walks:
                if nwalk % 2 == 0:
                    plot_walk_points(walk, map_handle, 'blue', sb.linewidth)
                else:
                    plot_walk_points(walk, map_handle, 'red', sb.linewidth)
            else:
                plot_walk_points(walk, map_handle, sb.linecolour, sb.linewidth)
    else:
        for walk_points in walk_points_all:
            walk_data = []
            for _, group in walk_points:
                walk_data.append(group[['lat', 'lon']].values.tolist())
            for nwalk, walk in enumerate(walk_data):
                plot_walk_points(walk, map_handle, sb.linecolour, sb.linewidth)

    map_handle.fit_bounds(map_handle.get_bounds())

    #TODO: Change the following to .format() and .join() not string "addition"

    #st.write('Total time: ' + str(total_time))
    #st.write('Total distance (km): ' + str(int(total_distance)))

    folium_static(map_handle, width=800, height=650)

    return map_handle
    #return map_handle, walk_data, walk_date, walk_points

# Cell

def notebook_mainscreen(APP_NAME, sb):
    print(APP_NAME)

    all_walks_df = load_cached_walking_data()

    sb.datasize = all_walks_df.memory_usage(deep=True).sum() / 1024 / 1024

    walk_name = sb.walk_name[0:3]
    walk_name = 'GNW'

    # walk_points = all_walks_df[all_walks_df['WalkName']==walk_name][['lat', 'lon']].values.tolist()
    walk_points = all_walks_df[all_walks_df['WalkName']==walk_name].groupby('WalkNumber')[['lat', 'lon']]

    walk_data = []
    for _, group in walk_points:
        walk_data.append(group[['lat', 'lon']].values.tolist())

    # TODO: Need to plot sub-walks seperately to avoid ordering issues

    # total_time, total_distance, start_coord, end_coord = calc_walk_stats(walk_data)

    start_coord = (0, 0)

    map_handle = folium.Map(start_coord, zoom_start=13, detect_retina=True, control_scale=True)

    for walk in walk_data:
        plot_walk_points(walk, map_handle, sb.linecolour, sb.linewidth)
    map_handle.fit_bounds(map_handle.get_bounds())

    print(sb.walk_name)
    #print('Total time: ' + str(total_time))
    #print('Total distance (km): ' + str(int(total_distance)))

    #folium_static(map_handle)
    return map_handle, None, None, walk_points

# Cell

sb = app_sidebar(APP_NAME)

if in_notebook():
    map_handle, walk_data, walk_date, walk_points = notebook_mainscreen(APP_NAME, sb)
    walk_date
    display(map_handle)
else:
    map_handle, walk_data, walk_date, walk_points = app_mainscreen(APP_NAME, sb)