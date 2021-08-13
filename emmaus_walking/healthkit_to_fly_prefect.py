# %% [markdown]
# # Database - functions for data back-end / manipulations
# 
# This is using an alternate approach:
#   - I have exported all of my Apple healthfit data from the Health app to export.zip 
#   and then converted this to a SQLite database using `healthfit-to-sqlite`
#   - I am then creating a "published" version of this SQLite database using
#   Datasette.io
#   - I have a local version of this database running at http://localhost:8081/healthkit and
#   similarly I have an externally deployed version at https://my-healthkit-data.fly.dev
#   - I will then run queries against this database to build the cache file (or possibly a smaller custom sqlite file)
# 
# ## TODO
# * This is still a work in progress
# * Need to write the queries to marshall the data for each of the workouts within each group of walks
# * Then cache this data - maybe try another (small) sqlite db for the caching (instead of feather)
# * **NOTE: It looks like the queries are being truncated at 1000 values - need to fix**
# 

# %%
import os
import pandas as pd
from dateutil.parser import parse
import datetime as dt
import sqlite3 as sql
from pathlib import Path
import tomli
import klib
import subprocess
import pendulum
from sqlite_utils import Database
import reverse_geocoder as rg


import prefect
from prefect import Flow, task
from prefect.environments import LocalEnvironment
#from prefect.tasks.aws.s3 import S3Upload
from prefect.core.parameter import Parameter
from prefect.engine.results import LocalResult
from prefect.engine.executors import LocalDaskExecutor

# %%
@task(checkpoint=True, result=LocalResult(), target="{task_name}-{today}")
def convert_hk_export_zip_to_sqlite():
    #TODO: See existing function below - convert to Prefect style
    pass


# %% [markdown]
# [https://databooth.slite.com/api/s/note/MEQPRcLKFqUE6ko2vVp3Yr/Datasette-io-approach](https://databooth.slite.com/api/s/note/MEQPRcLKFqUE6ko2vVp3Yr/Datasette-io-approach) (Slite page)
# 
# e.g. start_datasette = subprocess.Popen('datasette ' + db_name + ' -m aus-covid-datasette-meta.json', stdout=subprocess.PIPE, shell=True)

# %%
HEALTHKIT_DATA_PATH = Path("/Users/mjboothaus/data/healthkit")
export_zip = HEALTHKIT_DATA_PATH / "export.zip"


# %%
def convert_healthkit_export_to_sqlite(export_zip):
    zip_file = export_zip.as_posix()
    if export_zip.exists() == False:
        print(zip_file, ": not found")
        return None, zip_file + ": not found"
    zip_file_date = pendulum.instance(dt.datetime.fromtimestamp(export_zip.stat().st_ctime))

    db_file = zip_file.replace("export.zip", "healthkit.db")
    if Path(db_file).exists() == True:
        Path(db_file).unlink()
    sp_cmd = "pipx run healthkit-to-sqlite " + zip_file + " " + db_file
    print(sp_cmd)
    print('---------------------------------------------------------------------------------------------')
    print('Please wait: converting healthkit export.zip to sqlite database (takes just over a minute)...')

    sp = subprocess.Popen(sp_cmd, stdout=subprocess.PIPE, shell=True)
    (sp_output, sp_err) = sp.communicate()  

    #This makes the wait possible
    sp_status = sp.wait()

    db_file_with_date = db_file.replace(".db", "_" + zip_file_date.to_date_string().replace("-", "_") + ".db")
    
    export_zip.rename(zip_file.replace(".zip", "_" + zip_file_date.to_date_string().replace("-", "_") + ".zip"))
    Path(db_file).rename(db_file_with_date)

    return db_file_with_date, sp_output


# %%
db_file, output = convert_healthkit_export_to_sqlite(export_zip)


# %% [markdown]
# ## Look at the HealthKit database via Datasette.io (and try an reduce to just needed data)

# %%
print("datasette " + db_file + " --setting sql_time_limit_ms 5000  --setting max_returned_rows 10000 &")


# %%
def create_df_from_sql_query_in_file(filename_dot_sql, conn, parse_dates):
# Read the sql file
    query_file = get_project_root_alternate() / "sql" / filename_dot_sql

    with open(query_file, 'r') as query:
        # connection == the connection to your database
        sql_text = query.read()
        print(sql_text)
        df = pd.read_sql_query(sql_text, conn, parse_dates=parse_dates)
    return df


# %%
db = Database(db_file)


# %%
workouts_df = create_df_from_sql_query_in_file("select_star_walking_workouts.sql", db.conn, ['startDate', 'endDate'])

# %%
# Trying to find the start point in each walk workout -- as date is not a date field in db not clear if sort by date and limit 1 will work
# might need to import table to pandas convert types and then export to db before doing query. Else use sqlite_utils to change column types.

start_point_df = create_df_from_sql_query_in_file("select_start_point_workout.sql", db.conn, ['date'])
finish_point_df = create_df_from_sql_query_in_file("select_finish_point_workout.sql", db.conn, ['date'])

# %%
walk_info_df = start_point_df.merge(finish_point_df, how='inner', on='workout_id')


# %%
def get_location(latitude, longitude):
    location = rg.search((latitude, longitude))
    return [location[0]['name'], location[0]['admin1'], location[0]['cc']]


# %%
walk_info_df['start_location'] = walk_info_df.apply(lambda row: get_location(float(row['start_latitude']), float(row['start_longitude'])), axis=1)
walk_info_df['finish_location'] = walk_info_df.apply(lambda row: get_location(float(row['finish_latitude']), float(row['finish_longitude'])), axis=1)

# %%
def calculate_elapsed_time_minutes(finish_datetime, start_datetime):
    dt = pendulum.parse(finish_datetime) - pendulum.parse(start_datetime)
    return dt.in_seconds() / 60 / 60


# %%
walk_info_df['elapsed_time_hours'] = walk_info_df.apply(lambda row: calculate_elapsed_time_minutes(row['finish_datetime'], row['start_datetime']), axis=1)
walk_info_df['start_datetime'] = walk_info_df['start_datetime'].apply(lambda dt: pendulum.parse(dt, tz="Australia/Sydney").to_datetime_string())    # TODO: Need to convert from UTC to Sydney local time?

# %%
walk_info_df = walk_info_df.merge(workouts_df, how="inner", on="workout_id")


# %%
walk_info_df['startDate'] = walk_info_df['startDate'].apply(lambda dt: pendulum.instance(dt).to_datetime_string()) 
walk_info_df['endDate'] = walk_info_df['endDate'].apply(lambda dt: pendulum.instance(dt).to_datetime_string())


# %%
walk_info_df.to_excel('walk_info_df.xlsx', index=False)

# %%
workouts_df_cleaned = klib.data_cleaning(workouts_df)

# %%
workouts_csv = HEALTHKIT_DATA_PATH / "workouts.csv"

workouts_df_cleaned.to_csv(workouts_csv, index=False)


# %%
tables_df = create_df_from_sql_query_in_file("list_all_tables.sql", db.conn)

# %%


# %% [markdown]
# ### Looking at sqlite version of the cached data derived from individual walk files in walk groups

# %%
db_file = Path('emmaus-walking-db.sqlite')


# %%
print("datasette " + db_file + " &")


# %%
LOCAL_DB_URL = 'http://localhost:8081/'
HOSTED_DB_URL = 'https://my-healthkit-data.fly.dev/'


# %%
url_CSV = 'http://localhost:8081/healthkit.csv?sql=select%0D%0A++id%2C%0D%0A++workoutActivityType%2C%0D%0A++duration%2C%0D%0A++durationUnit%2C%0D%0A++totalDistance%2C%0D%0A++totalDistanceUnit%2C%0D%0A++totalEnergyBurned%2C%0D%0A++totalEnergyBurnedUnit%2C%0D%0A++sourceName%2C%0D%0A++sourceVersion%2C%0D%0A++creationDate%2C%0D%0A++startDate%2C%0D%0A++endDate%2C%0D%0A++metadata_HKTimeZone%2C%0D%0A++metadata_HKWeatherTemperature%2C%0D%0A++metadata_HKWeatherHumidity%2C%0D%0A++device%2C%0D%0A++metadata_HKElevationAscended%2C%0D%0A++metadata_HKAverageMETs%0D%0Afrom%0D%0A++workouts%0D%0Aorder+by%0D%0A++id%0D%0Alimit%0D%0A++101'


# %%
url_CSV2 = 'http://localhost:8081/healthkit.csv?sql=select%0D%0A++id%2C%0D%0A++workoutActivityType%2C%0D%0A++duration%2C%0D%0A++durationUnit%2C%0D%0A++totalDistance%2C%0D%0A++totalDistanceUnit%2C%0D%0A++totalEnergyBurned%2C%0D%0A++totalEnergyBurnedUnit%2C%0D%0A++sourceName%2C%0D%0A++sourceVersion%2C%0D%0A++creationDate%2C%0D%0A++startDate%2C%0D%0A++endDate%2C%0D%0A++metadata_HKTimeZone%2C%0D%0A++workout_events%2C%0D%0A++metadata_HKWeatherTemperature%2C%0D%0A++metadata_HKWeatherHumidity%2C%0D%0A++device%2C%0D%0A++metadata_HKElevationAscended%2C%0D%0A++metadata_HKAverageMETs%2C%0D%0A++metadata_HKMaximumSpeed%2C%0D%0A++metadata_HKAverageSpeed%0D%0Afrom%0D%0A++workouts%0D%0Awhere%0D%0A++workoutActivityType+in+%28%3Ap0%2C+%3Ap1%29%0D%0Aorder+by%0D%0A++creationDate%0D%0Alimit%0D%0A++101&p0=HKWorkoutActivityTypeWalking&p1=HKWorkoutActivityTypeHiking&_size=max'


# %%
workouts_df = pd.read_csv(url_CSV)

#print((LOCAL_DB_URL + 'workout.json'))
#workout_df = pd.read_json(LOCAL_DB_URL + 'workouts.json')

# %%
workouts_clean_df = klib.data_cleaning(workouts_df)


# %%
workouts_fly_df = pd.read_csv(url_CSV.replace(LOCAL_DB_URL, HOSTED_DB_URL))

# %%
workout_points_SQL = 'http://localhost:8081/healthkit.csv?sql=select%0D%0A++rowid%2C%0D%0A++date%2C%0D%0A++latitude%2C%0D%0A++longitude%2C%0D%0A++altitude%2C%0D%0A++speed%0D%0Afrom%0D%0A++workout_points%0D%0Awhere%0D%0A++workout_id+%3D+%22'
workout_id = 'a34036ff616122952fa67c9bc11a493f8642dd7c' + '%22'

workout_points_df = pd.read_csv(workout_points_SQL + workout_id, parse_dates=True)


# %%
WALK_DETAILS_FILE = 'walk_details.toml'
walk_details = Path('../' + WALK_DETAILS_FILE)


# %%
with open(walk_details, encoding="utf-8") as f:
    walk_details_dict = tomli.load(f)


# %%
walk_details_dict


# %%
pd.DataFrame(walk_details_dict, )



# %%
def create_walk_cached_data_for_app(db_file, n_rows_used=5):
    # read in all of the walks data and sample at an appropriate frequency and cache for faster use in the app
    db_conn = sql.connect(db_file)
    walk_df = pd.read_sql_query('SELECT * FROM walks', db_conn)

    UNUSED_COLUMNS = ['dist', 'speed']

    walk_df.drop(UNUSED_COLUMNS, axis=1, inplace=True)
    walk_df.dropna(inplace=True)      # TODO: Check why there are a few NaNs
    walk_df = walk_df.iloc[::n_rows_used].reset_index()    # downsample

    walk_df.to_feather(Path(db_file.as_posix().replace('.db', '.cache.feather')))
    
    return walk_df


# %%
# Not working yet -- this is the alternate approach to using the individual .FIT files
# walk_df = create_walk_cached_data_for_app(db_file, 10)


# %%
# walk_df[walk_df['lat'].isna()]


# %%
Path(db_file.as_posix().replace('.sqlite', '.cache.feather'))

# %%
@task
def datasette_publish_to_fly(db_name):
    fly_app_name = db_name.replace('.sqlite', '-datasette')
    print("datasette publish fly " + db_name + " --app=" + fly_app_name + " -m COVID-19-Datasette-metadata.json")
    return fly_app_name

    #TODO: Shell commands in prefect API + logging


# %%
def create_flow() -> Flow:
    #local_parallelizing_environment = LocalEnvironment(executor=LocalDaskExecutor())
    FLOW_NAME = "HealthKit (export.zip) to SQLite DB then publis to Fly"

    #with Flow(FLOW_NAME, environment=local_parallelizing_environment) as flow:
    with Flow(FLOW_NAME) as flow:
        #country = Parameter("country", default=DEFAULT_COUNTRY)
        #bucket = Parameter("bucket", default=DEFAULT_BUCKET)
        
        covid_data = download_data()
        clean_data = clean_data_klib(covid_data)
        db_name = push_data_to_sqlite(clean_data)
        fly_app_name = datasette_publish_to_fly(db_name)

        print(fly_app_name)

        #filtered_covid_df = filter_data(covid_df, country)
        #prepared_df = enrich_data(filtered_covid_df)
        #aggregated_df = aggregate_data(prepared_df)
        #print_data(aggregated_df)
        #csv_results = prepare_data_for_upload(aggregated_df)
        #upload_to_s3(csv_results["csv"], csv_results["filename"], bucket=bucket)

    return flow

# %%
if __name__ == "__main__":
    create_flow()
