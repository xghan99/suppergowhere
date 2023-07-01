from mrt.mrt import MRTLoader as MRT
from places.place_searcher import PlaceSearcher
from bigquery.bq_wrapper import BQWrapper

import json
from dash import Dash, html, Input, Output, State, ctx, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

local_testing = False

app = Dash(__name__, suppress_callback_exceptions=True)
project_id = 'suppergowhere'

# Load the day mapping
with open("../data/mapping.json", "r") as f:
    day_mapping = json.load(f)

# Load the MRT data
mrt = MRT("../data/mrt_lrt_data.csv")
mrt_coord_dict = mrt.get_mrt_coord_dict(mrt.data)

# init place searcher and BQ wrapper
place_searcher = PlaceSearcher(local_testing=True, mrt_coord_dict=mrt_coord_dict)
bq = BQWrapper(project_id=project_id, local_testing=local_testing)

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
    dcc.Loading(children=html.Div(id='output'), type="circle"),
    html.Br(),
    html.Div(id='selected_place'),
    html.Div(id="supper_locations")
],
    className='container'
)


@app.callback(
    Output('output', 'children'),
    Input('submit', 'n_clicks'),
    State('day', 'value'),
    State('time', 'value'),
)
def update_output(n_clicks, day_value, time_value):
    global day_mapping
    if n_clicks > 0:
        day = day_mapping[day_value]
        time = int(time_value[1])
        # TODO: refactor out the query
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
        count = 0
        for i in result['station_name']:
            child_components.append(html.Button(
                f'{i}', n_clicks=0, value=f'{i}', id=f'places_{count}'))
            count += 1
        return html.Div(children=child_components)


@app.callback(
    Output('selected_place', 'children'),
    Input('places_0', 'n_clicks'),
    Input('places_1', 'n_clicks'),
    Input('places_2', 'n_clicks'),
    Input('places_3', 'n_clicks'),
    Input('places_4', 'n_clicks'),
    State('places_0', 'value'),
    State('places_1', 'value'),
    State('places_2', 'value'),
    State('places_3', 'value'),
    State('places_4', 'value'),
    State('day', 'value'),
    State('time', 'value'),
    prevent_initial_call=True
)
def suggest_all_places(p0, p1, p2, p3, p4, v0, v1, v2, v3, v4, day, time):
    day = day_mapping[day]
    triggered_id = ctx.triggered_id
    if p0+p1+p2+p3+p4 > 0:
        if triggered_id == 'places_0':
            return place_searcher.suggest_place(v0, day, time)
        if triggered_id == 'places_1':
            return place_searcher.suggest_place(v1, day, time)
        if triggered_id == 'places_2':
            return place_searcher.suggest_place(v2, day, time)
        if triggered_id == 'places_3':
            return place_searcher.suggest_place(v3, day, time)
        if triggered_id == 'places_4':
            return place_searcher.suggest_place(v4, day, time)


if __name__ == '__main__':
    if not local_testing:
        app.run_server(host='0.0.0.0', port=8080, debug=True)
    else:
        app.run_server(debug=True)
