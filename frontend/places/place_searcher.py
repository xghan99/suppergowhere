import os
import requests
from datetime import time
from dash import html
import pandas as pd
import dash_bootstrap_components as dbc
from bigquery.bq_wrapper import BQWrapper

class PlaceSearcher:
    def __init__(self, local_testing: bool, mrt_coord_dict: dict, project_id: str):
        self.mrt_coord_dict = mrt_coord_dict
        self.API_KEY = os.environ.get('maps_api_key')
        self.project_id = project_id
        self.local_testing = local_testing

    """Checks if a place is open at a given day and time

    :param api_key: Google Maps API key :class:`str`
    :param place_id: Google Maps Place ID :class:`str`
    :param day: Day of the week :class:`int`
    :param timing: Time of the day :class:`str`

    :return: :class:`bool`
    """

    def _is_place_open(
            self,
            api_key: str,
            place_id: str,
            day: int,
            timing: str
    ) -> bool:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?key={api_key}&place_id={place_id}"
        try:
            # Check if the API request was successful
            response = requests.get(url)
        except requests.exceptions.Timeout:
            retry_attempts = 5
            for _ in range(retry_attempts):
                try:
                    response = requests.get(url)
                    break
                except requests.exceptions.Timeout:
                    continue
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            print("Bad URL")
            return False
        except requests.exceptions.RequestException as e:
            print("Error in request", e)
            return False

        if response.status_code != 200 and data["status"] != "OK":
            print("Error in request", response.status_code)
            return False

        # catch any json parsing errors
        try:
            data = response.json()
        except ValueError:
            print("Error in request", response.status_code)
            return False
        #Google Maps follows a different convention for dates where 'Sunday' = 0 and not 'Monday'
        day = (day+1) % 7

        result = data["result"]

        # Check if the opening hours and periods info are available
        if "opening_hours" in result and "periods" in result["opening_hours"]:
            opening_hours = result["opening_hours"]

            for period in opening_hours["periods"]:
                if period["open"]["day"] == day:
                    open_time = time(int(period["open"]["time"][:2]), 0)
                    close_time = time(int(period["close"]["time"][:2]), 0)
                    query_time = time(int(timing[:2]), 0)

                    if open_time < close_time:
                        if (query_time >= open_time) and (query_time <= close_time):
                            return True
                        else:
                            continue
                    else:
                        if (query_time >= open_time) or (query_time <= close_time):
                            return True
                        else:
                            continue
            return False

        # assume the place is open 24/7 if result unavailable
        else:
            print("Opening hours or periods not available, defaulting to 24/7")
            return True

    """Suggests a supper place based on various criteria

    :param mrt_coord_dict: Dictionary of MRT station names and their coordinates :class:`dict`
    :param place: MRT station name :class:`str`
    :param day: Day of the week :class:`int`
    :param time: Time of the day :class:`str`
    :param radius: Radius of the search area :class:`int`

    :return: :class:`str`
    """

    def suggest_place(self,
                      place: str,
                      day: int,
                      time: str,
                      radius: int = 500,
                      keyword: str = "restaurant"):
        
        location = self.mrt_coord_dict[place]
        table = 'supper_locations.supper_location'
        bq = BQWrapper(local_testing=self.local_testing, project_id=self.project_id)
        #Attempt to get cached supper spots and their ratings from BigQuery
        query = f"SELECT name, rating FROM {table} WHERE day  = {day} AND time = '{time}' AND place = '{place}'"
        query_job = bq.query(query)
        result = pd.DataFrame(query_job.to_dataframe())
        result.reset_index(inplace = True, drop = True)
        #Cached results exists                  
        if result.shape[0]>0:
            return self.generate_output(result)
        #Cache does not exist: call Maps API to get supper locations and cache the results
        else:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?type={keyword}&location={location[0]}%2C{location[1]}&radius={radius}&key={self.API_KEY}"
            headers = {}
            payload = {}
            try:
                response = requests.request(
                    "GET", url, headers=headers, data=payload)
            except requests.exceptions.Timeout:
                retry_attempts = 5
                for _ in range(retry_attempts):
                    try:
                        response = requests.request(
                            "GET", url, headers=headers, data=payload)
                        break
                    except requests.exceptions.Timeout:
                        continue
            except requests.exceptions.TooManyRedirects:
                # Tell the user their URL was bad and try a different one
                print("Bad URL")
                return False
            except requests.exceptions.RequestException as e:
                print("Error in request", e)
                return False

            if response.status_code != 200:
                print("Error in request", response.status_code)
                return False

            try:
                json_response = response.json()
            except ValueError:
                print("Error in request", response.status_code)
                return False

            names = [i['name'] for i in json_response['results']]
            ratings = [i['rating']
                       if 'rating' in i else 0.0 for i in json_response['results']]
            place_ids = [i['place_id'] for i in json_response['results']]
            is_open = map(lambda place_id:
                          self._is_place_open(
                              self.API_KEY,
                              place_id,
                              day,
                              time),
                          list(place_ids)
                          )
            result_dict = {'name':list(names),'rating':list(ratings),'is_open':list(is_open)}
            result_df = pd.DataFrame(result_dict)
            #Only keeps results for restaurants that are open at the specified time
            result_df = result_df[result_df['is_open']]
            result_df['day'] = day
            result_df['time'] = time
            result_df['place'] = place
            result_df = result_df.drop('is_open', axis = 1)
            result_df.reset_index(inplace = True, drop = True)
            #Cache results
            job = bq.client.load_table_from_dataframe(result_df,table)
            return self.generate_output(result_df)

    def generate_output(self,df):
        cards = []
        names = df['name']
        ratings = df['rating']
        for i in range(len(df)):
            cards.append(dbc.Card([dbc.CardBody([html.H4(f"{names[i]}"),html.P(f"Rating: {ratings[i]}/5")])],class_name = "card"))
            cards.append(html.Br())
            
        if cards:
            return cards
        else:
            return "Nothing to suggest!"
