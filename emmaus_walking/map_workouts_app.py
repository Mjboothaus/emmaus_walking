from numpy import empty
import streamlit as st
import pandas as pd
from pathlib import Path
from sqlite_utils import Database
from streamlit_folium import folium_static
import folium

st.set_page_config(layout="wide")

def plot_walk_points(walk_points, map_handle, linecolour, linewidth):
    folium.PolyLine(walk_points, color=linecolour, weight=linewidth).add_to(map_handle)

db = Database(Path("/Users/mjboothaus/data/healthkit/healthkit_2021_07_31.db"))

# Load some example data.
DATA_URL = Path("nbs/start_point_df.xlsx")
data = st.cache(pd.read_excel)(DATA_URL)

# Select some rows using st.multiselect. This will break down when you have >1000 rows.
st.write('### Full Dataset', data)
selected_indices = st.multiselect('Select rows:', data.index)

if selected_indices != []:

    st.write('### Selected Rows')

    for row in selected_indices:
        selected_row = data.loc[row]
        st.write(selected_row)

        query = 'SELECT latitude, longitude FROM workout_points WHERE workout_id = "'
        query += selected_row['workout_id'] + '"'

        data_df = pd.read_sql_query(query, db.conn)

        start_coord = (0, 0)

        map_handle = folium.Map(start_coord, zoom_start=13, detect_retina=True, control_scale=True)
        plot_walk_points(data_df.values, map_handle, 'blue', 3)
        map_handle.fit_bounds(map_handle.get_bounds())
        folium_static(map_handle, width=500, height=200)