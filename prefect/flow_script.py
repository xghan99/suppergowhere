from prefect import flow, task
import requests
import pandas as pd
import numpy as np
import geopy.distance
import pytz
from datetime import datetime, date
from prefect_gcp import GcpCredentials



# Helper Functions
# This function computes the number of taxis within 500m of an MRT station
# x = mrt station coordinates, y = taxi coordinates
def get_num_taxis(x,y):
  dists = y.map(lambda z: geopy.distance.geodesic(z,x).m)
  num_taxis = (dists<500).sum()
  return num_taxis

# Extract
# This function extracts the coordinates of taxis from Data.gov.sg API at the given datetime and converts them into a Pandas dataframe
@task(log_prints = True)
def get_data_from_api(year,month,day,hour):
    query_string = f"{year}-{month:02}-{day:02}T{hour:02}%3A00%3A00"
    content = requests.get(f"https://api.data.gov.sg/v1/transport/taxi-availability?date_time={query_string}")
    data = content.json()['features'][0]['geometry']['coordinates']
    df = pd.DataFrame(data, columns = ['lng','lat'])
    # Reordered columns to follow the format of MRT coordinates
    df = df[['lat','lng']]
    # Created 'combined' column as map can only be run on a single column
    df['combined'] = df.values.tolist()
    return df

# Transform
# This function returns the dataframe which shows the number of taxis near each MRT station at the specific date and time
# day, hour and station_name are the columns which the num_taxis are averaged on
@task(log_prints = True)
def compute_taxis_per_station(mrt_data,df,hour,weekday, today_date):
    new_df = mrt_data.copy()
    new_df['num_taxis'] = new_df['combined'].map(lambda x: get_num_taxis(x, df['combined']))
    new_df['hour'] = hour
    new_df['day'] = weekday
    new_df['date'] = today_date
    new_df['date'] = pd.to_datetime(new_df['date'], infer_datetime_format = True)
    result = new_df[['date','station_name','day','hour','num_taxis']]
    return result

# Load to BQ
# This function loads the transformed dataframe into Google BigQuery
@task
def load_to_bq(df):
  gcp_credentials_block = GcpCredentials.load("supper-01")
  df.to_gbq(destination_table = "taxi_mrt_stations.frequency", project_id = "suppergowhere",
            credentials = gcp_credentials_block.get_credentials_from_service_account(),
            if_exists = "append")

# Main Prefect ETL Flow    
@flow
def main_flow():
    #Reading MRT Station Coordinates
    mrt_data = pd.read_csv("mrt_lrt_data.csv")
    # Filter to remove LRT stations
    mrt_data = mrt_data[mrt_data['type'] == 'MRT']
    # Combining lat and lng so that map function can be applied to a single column
    mrt_data['combined'] = mrt_data[['lat','lng']].values.tolist()
    # Setting Arguments
    now = datetime.now(pytz.timezone("singapore"))
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    weekday = now.weekday()
    today_date = date.today()
    #Running ETL Tasks
    df = get_data_from_api(year,month,day,hour)
    df_transformed = compute_taxis_per_station(mrt_data,df,hour, weekday, today_date)
    load_to_bq(df_transformed)


