from mrt.mrt import MRTLoader as MRT
from places.place_searcher import PlaceSearcher
from bigquery.bq_wrapper import BQWrapper
import os
import json
from dash import Dash, html, Input, Output, State, ctx, dcc

local_testing = os.environ.get('local_testing')=="True"

app = Dash(__name__, suppress_callback_exceptions=True, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

if not local_testing:
    server = app.server
    
project_id = 'suppergowhere'  #For Google Cloud Platform

# Load the day mapping
with open("./data/mapping.json", "r") as f:
    day_mapping = json.load(f)

# Load the MRT Stations' coordinates data
mrt = MRT("./data/mrt_lrt_data.csv")
mrt_coord_dict = mrt.get_mrt_coord_dict(mrt.data)


# init PlaceSearcher (for getting supper spots) and BigQuery (for getting top 5 MRT stations/ cached supper spots) Wrapper classes
place_searcher = PlaceSearcher(
    local_testing=local_testing, mrt_coord_dict=mrt_coord_dict, project_id = project_id)

bq = BQWrapper(local_testing=local_testing, project_id=project_id)


app.layout = html.Div(children=[
    html.H1(children='SupperGoWhere', className='title'),
    html.Div(children='Where to have supper so that you can afford the Grab home?',
             className='subtitle'),
    html.Br(),
    html.Div(children='Enter the day and time you are planning to head home',
             className='instructions'),
    html.Div(
        children=[
            dcc.Dropdown([day for day in day_mapping.keys()],
                         placeholder='Select the Day',
                         id='day',
                         clearable=False),
            dcc.Dropdown([f'0{str(h)}:00' for h in range(0, 6)],
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
    dcc.Loading(children=html.Div(id='output'), type="circle"),
    html.Br(),
    dcc.Loading(children=html.Div(id ="selected_place" ), type = "circle")
],
    className='container'
)

#This runs upon user submitting the day and time
@app.callback(
    Output('output', 'children'),
    Input('submit', 'n_clicks'),
    State('day', 'value'),
    State('time', 'value'),
)
def update_output(n_clicks, day_value, time_value):
    global day_mapping
    if n_clicks > 0:
        #Convert day to a numerical value ('Monday' = 0 etc.)
        day = day_mapping[day_value]
        time = int(time_value[1])
        #Query for top 5 MRT stations with highest average number of taxis around
        query = f"SELECT station_name, AVG(num_taxis) as avg_taxi \
            FROM taxi_mrt_stations.frequency \
            WHERE day = {day} AND hour = {time} \
            GROUP BY station_name, day, hour \
            ORDER BY avg_taxi DESC \
            LIMIT 5"
        query_job = bq.query(query)
        result = query_job.to_dataframe()
        child_components = [
            html.Div("The top 5 MRT stations to have supper nearby are: ")]
        tabs = []
        count = 0  
        initial_name = ''
        #Create tabs for each of the top 5 results
        for i in result['station_name']:
            if count==0:
                initial_name = i #Set the default tab to be the MRT station with the highest average number of taxis around
            tabs.append(dcc.Tab(label = f'{i}', value = f'{i}'))
            count+=1
        child_components.append(dcc.Tabs(children=tabs, id="selected_location", value = initial_name))
        return html.Div(children=child_components)

#This runs upon user clicking on an MRT stataion
@app.callback(
    Output('selected_place', 'children'),
    Input('selected_location', 'value'),
    State('day', 'value'),
    State('time', 'value'),
    prevent_initial_call=True  #This ensures that the function does not run when user first enters the page
)
def suggest_all_places(loc, day, time):
    day = day_mapping[day]
    return place_searcher.suggest_place(loc,day,time)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
    
