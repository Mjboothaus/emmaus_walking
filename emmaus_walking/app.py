# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/88_app.ipynb (unless otherwise specified).

__all__ = ['plot_walk', 'plot_entire_walk', 'plot_walk_points', 'SideBar', 'app_sidebar', 'app_mainscreen',
           'notebook_mainscreen', 'sb']

# Cell
import numpy as np
import pandas as pd
import datetime as dt
import streamlit as st
from streamlit_folium import folium_static
import folium
from PIL import Image
from IPython.display import display
#import os, io
#import activityio as aio
#from dateutil.parser import parse

from core import in_notebook
from datapipe import load_and_cache_raw_walk_data, calc_walk_stats

# Internal Cell

DATA_INFO = 'Health Fit / Apple Watch (Author)'
AUTHOR_INFO = 'AUTHOR: [Michael J. Booth](https://about.me/mjboothaus)'
APP_NAME = 'Emmaus Walking Mapping App'

st.beta_set_page_config(page_title=APP_NAME)

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
    linewidth = 6
    linecolour = 'yellow'


def app_sidebar(APP_NAME):
    WALK_NAME = ['B2M: Bondi to Manly', 'GNW: Great North Walk', 'GWW: Great West Walk']
    IMAGE_PATH = '/Users/mjboothaus/iCloud/Code/Github/emmaus_walking/emmaus_walking/resources'
    sb = SideBar()

    aw_image = Image.open(IMAGE_PATH + '/AppleWatchExercise.jpeg')
    st.sidebar.image(image=aw_image, use_column_width=True, output_format='JPEG')

    hf_image = Image.open(IMAGE_PATH + '/HealthFitLogo.png')
    st.sidebar.image(image=hf_image, use_column_width=True, output_format='PNG')

    st.sidebar.info(APP_NAME)
    st.sidebar.markdown(sb.author)
    st.sidebar.markdown(sb.datasource)
    st.sidebar.info(sb.data_title)
    #st.sidebar.markdown('Datasize: ' + str(sb.datasize))
    sb.walk_name = st.sidebar.selectbox('Choose a walk', WALK_NAME, 0)
    sb.linewidth = st.sidebar.slider('Line width:', min_value=1, max_value=10, value=6)
    sb.linecolour = st.sidebar.radio('Line colour:', ['yellow', 'blue'], 0)

    return sb

# Cell
def app_mainscreen(APP_NAME, sb):

    #st.title(APP_NAME)
    st.header(sb.walk_name)
    # Load walking data
    sample_freq=50
    walk_data, walk_date, walk_files, walk_points = load_and_cache_raw_walk_data(sb.walk_name, sample_freq)
    total_time, total_distance, start_coord, end_coord = calc_walk_stats(walk_data)

    map_handle = folium.Map(start_coord, zoom_start=13, detect_retina=True, control_scale=True)
    plot_walk_points(walk_points, map_handle, sb.linecolour, sb.linewidth)
    map_handle.fit_bounds(map_handle.get_bounds())

    #TODO: Change the following to .format() and .join() not string "addition"

    st.write('Total time: ' + str(total_time))
    st.write('Total distance (km): ' + str(int(total_distance)))

    folium_static(map_handle, width=800, height=650)

    return map_handle, walk_data, walk_date, walk_points

# Cell
def notebook_mainscreen(APP_NAME, sb):
    print(APP_NAME)

    # Load walking data
    sample_freq=50
    walk_data, walk_date, walk_files, walk_points = load_and_cache_raw_walk_data(sb.walk_name, sample_freq)
    total_time, total_distance, start_coord, end_coord = calc_walk_stats(walk_data)

    map_handle = folium.Map(start_coord, zoom_start=13, detect_retina=True, control_scale=True)
    plot_walk_points(walk_points, map_handle, sb.linecolour, sb.linewidth)
    map_handle.fit_bounds(map_handle.get_bounds())

    print(sb.walk_name)
    print('Total time: ' + str(total_time))
    print('Total distance (km): ' + str(int(total_distance)))

    #folium_static(map_handle)
    return map_handle, walk_data, walk_date, walk_points

# Cell

sb = app_sidebar(APP_NAME)

if in_notebook():
    map_handle, walk_data, walk_date, walk_points = notebook_mainscreen(APP_NAME, sb)
    walk_date
    display(map_handle)
else:
    map_handle, walk_data, walk_date, walk_points = app_mainscreen(APP_NAME, sb)