from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime
from api_key import api_key

app = Flask(__name__)

# Fetch current vehicles locations 
url = "https://api.um.warszawa.pl/api/action/busestrams_get"
params = {
    "resource_id": "f2e5503e-927d-4ad3-9500-4ab9e55deb59",  # resource id given by the API
    "apikey": api_key,
    "type": 1,  # 1 - bus, 2 - tram
}
locations = requests.get(url, params=params)
locations_df = pd.json_normalize(locations.json()["result"])
locations_df.rename(columns={"Lat": "Latitude", "Lon": "Longitude"}, inplace=True)
locations_df["Label"] = locations_df["Lines"].astype(str) + "/" + locations_df["Brigade"].astype(str)
locations_df["Latitude"] = locations_df["Latitude"].astype(str)
locations_df["Longitude"] = locations_df["Longitude"].astype(str)
locations_df['Time'] = pd.to_datetime(locations_df['Time'])
current_time = datetime.now()
time_diff = current_time - locations_df['Time']
locations_df = locations_df[time_diff <= pd.Timedelta(seconds=30)]

# Fetch routes from the API
url_routes = "https://api.um.warszawa.pl/api/action/public_transport_routes"
params_routes = {
    "apikey": api_key,
}
routes_response = requests.get(url_routes, params=params_routes)
routes = routes_response.json()["result"]

# Sort routes: First numeric routes in ascending order, then non-numeric routes alphabetically
def sort_routes(route_dict):
    numeric_routes = sorted([route for route in route_dict.keys() if route.isdigit()], key=int)
    alphanumeric_routes = sorted([route for route in route_dict.keys() if not route.isdigit()])
    return numeric_routes + alphanumeric_routes

sorted_routes = sort_routes(routes)

# Fetch stops data
url_stops = "https://api.um.warszawa.pl/api/action/dbstore_get"
params_stops = {
    "id": "ab75c33d-3a26-4342-b36a-6e5fef0a3ac3",  # resource id for stops
    "apikey": api_key,
}
stops_response = requests.get(url_stops, params=params_stops)
rows = [
    {entry["key"]: entry["value"] for entry in item["values"]}
    for item in stops_response.json()["result"]
]
stops_df = pd.DataFrame(rows)
stops_df.rename(columns={"szer_geo": "Latitude", "dlug_geo": "Longitude"}, inplace=True)
stops_df["Label"] = stops_df["nazwa_zespolu"].astype(str) + " " + stops_df["slupek"].astype(str)

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_route = request.args.get('route', '159')  # Default route 159

    # Get the stops for the selected route
    stops_for_line = []
    for i, j in routes.get(selected_route, {}).items():
        for k, l in j.items():
            stops_for_line.append(l)

    stops_for_line = pd.DataFrame(stops_for_line)
    stops_for_line = stops_for_line.drop(columns=["odleglosc", "ulica_id", "typ"]).drop_duplicates()
    stops_for_line = pd.merge(stops_for_line, stops_df, left_on=["nr_zespolu", "nr_przystanku"], right_on=["zespol", "slupek"], how="left")

    locations_for_line = locations_df[locations_df["Lines"] == selected_route]
    
    # Convert to dictionary for template
    stops_locations = stops_for_line.to_dict(orient='records')
    vehicle_locations = locations_for_line.to_dict(orient="records")

    return render_template('map.html', stops_locations=stops_locations, routes=sorted_routes, selected_route=selected_route, vehicle_locations=vehicle_locations)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
