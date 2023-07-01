import dash
from dash import html, Input, Output, State, callback, ctx, dcc, dash_table
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from datetime import time
import os

local_testing = False
app = dash.Dash(__name__,suppress_callback_exceptions=True)
mrt_stations = pd.read_csv("mrt_lrt_data.csv")
mrt_coord_dict = dict(zip(mrt_stations.station_name,zip(mrt_stations.lat,mrt_stations.lng)))

if not local_testing:
    server = app.server
    
if local_testing:
    credentials = service_account.Credentials.from_service_account_file('')
#Private service account credentials: left blank as it is not required for deployment on Google Cloud App Engine due to ADC

project_id = 'suppergowhere'

if not local_testing:
    client = bigquery.Client(project=project_id)
else:
    client = bigquery.Client(project = project_id, credentials = credentials)
    
day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
               'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}

def is_place_open(api_key, place_id, day, timing):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?key={api_key}&place_id={place_id}"
    response = requests.get(url)
    data = response.json()
    day = (day+1)%7
    # Check if the API request was successful
    if response.status_code == 200 and data["status"] == "OK":
        result = data["result"]

        # Check if the opening hours information is available
        if "opening_hours" in result:
            opening_hours = result["opening_hours"]
            
            # Check if the opening hours for the specified day is available
            if "periods" in opening_hours:
                for period in opening_hours["periods"]:
                    if period["open"]["day"] == day:
                        open_time = time(int(period["open"]["time"][:2]),0)
                        close_time = time(int(period["close"]["time"][:2]),0)
                        query_time = time(int(timing[:2]),0)
                        if open_time < close_time:
                            if query_time>=open_time and query_time<=close_time:
                                return True
                            else:
                                continue
                        else:
                            if query_time>=open_time or query_time <= close_time:
                                return True
                            else:
                                continue
                return False
            else:
                return True

        # If the opening hours information is not available, assume the place is open 24/7
        else:
            return True

    # Handle errors or API request failures
    else:
        print("Error:", data["status"])
        return False

#Helper
def suggest_place(place, day, time):
    location = mrt_coord_dict[place]
    radius = 500
    keyword = "restaurant"
    if local_testing:
        API_KEY = ""
    else:
        API_KEY = os.environ.get('MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?type={keyword}&location={location[0]}%2C{location[1]}&radius={radius}&key={API_KEY}"
    headers = {}
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    json_response = response.json()
    names = [i['name'] for i in json_response['results']]
    ratings = [i['rating'] if 'rating' in i else 0.0 for i in json_response['results'] ]
    place_ids = [i['place_id'] for i in json_response['results']]
    is_open = map(lambda x:is_place_open(API_KEY,x,day,time),list(place_ids))
    dict_return = {'names':list(names), 'ratings':list(ratings),'is_open' :list(is_open)}
    df_return = pd.DataFrame(dict_return)
    print(df_return.columns)
    df_return = df_return[df_return['is_open']][['names','ratings']]
       
    return dash_table.DataTable(df_return.to_dict("records"))

app.layout = html.Div(children=[
    html.H1(children='SupperGoWhere', className='title'),
    html.Div(children='Where to have supper so that you can afford the Grab home?',
             className='subtitle'),
    html.Br(),
    html.Div(children='Enter the day and time you are planning to head home',
             className='instructions'),
    html.Div(
        children=[
            dcc.Dropdown(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                         placeholder='Select the Day',
                         id='day',
                         clearable=False),
            dcc.Dropdown(['00:00', '01:00', '02:00', '03:00', '04:00', '05:00'],
                         id='time',
                         placeholder='Select the Time',
                         clearable=False),
            html.Button('Go',
                        n_clicks=0,
                        id='submit'),
            
        ],
        id='user_input'
    ),
    html.Br(),
    dcc.Loading(children = html.Div(id='output'),type = "circle"),
    html.Br(),
    html.Div(id = 'selected_place'),
    html.Div(id = "supper_locations")
],
    className='container'
)

@app.callback(
    Output('output','children'),
    Input('submit', 'n_clicks'),
    State('day', 'value'),
    State('time', 'value'),
)
def update_output(n_clicks, day_value, time_value):
    global day_mapping
    global client
    if n_clicks > 0:
        day = day_mapping[day_value]
        time = int(time_value[1])
        query = f"SELECT station_name, AVG(num_taxis) as avg_taxi \
            FROM taxi_mrt_stations.frequency \
            WHERE day = {day} AND hour = {time} \
            GROUP BY station_name, day, hour \
            ORDER BY avg_taxi DESC \
            LIMIT 5"
        query_job = client.query(query)
        result = query_job.to_dataframe()
        child_components = [
            html.Div("The top 5 MRT stations to have supper nearby are: ")]
        count = 0
        for i in result['station_name']:
            child_components.append(html.Button(f'{i}', n_clicks = 0, value =  f'{i}', id = f'places_{count}'))
            count+=1
        return html.Div(children=child_components)

@app.callback(
    Output('selected_place','children'),
    Input('places_0','n_clicks'),
    Input('places_1','n_clicks'),
    Input('places_2','n_clicks'),
    Input('places_3','n_clicks'),
    Input('places_4','n_clicks'),
    State('places_0','value'),
    State('places_1','value'),
    State('places_2','value'),
    State('places_3','value'),
    State('places_4','value'),
    State('day','value'),
    State('time','value'),
    prevent_initial_call=True
)

def suggest_all_places(p0,p1,p2,p3,p4,v0,v1,v2,v3,v4,day,time):
    day = day_mapping[day]
    triggered_id = ctx.triggered_id
    if p0+p1+p2+p3+p4 > 0:
        if triggered_id == 'places_0':
            return suggest_place(v0,day,time)
        if triggered_id == 'places_1':
            return suggest_place(v1,day,time)
        if triggered_id == 'places_2':
            return suggest_place(v2,day,time)
        if triggered_id == 'places_3':
            return suggest_place(v3,day,time)
        if triggered_id == 'places_4':
            return suggest_place(v4,day,time)
            
    

if __name__ == '__main__':
    if not local_testing:
        app.run_server(host='0.0.0.0', port=8080, debug=True)
    else:
        app.run_server(debug=True)
