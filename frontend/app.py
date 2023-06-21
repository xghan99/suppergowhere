import dash
from dash import dcc
from dash import html, Input, Output, State, callback
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
app = dash.Dash(__name__)
server = app.server

#credentials = service_account.Credentials.from_service_account_file('')
#Private service account credentials: left blank as it is not required for deployment on Google Cloud App Engine due to ADC

project_id = 'suppergowhere'
client = bigquery.Client(project=project_id)
#client = bigquery.Client(project = project_id, credentials = credentials)
day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
               'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}

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
        for i in result['station_name']:
            child_components.append(html.Div(f"{i}"))
        return html.Div(children=child_components)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
