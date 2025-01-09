from flask import Flask, render_template, request
import pandas as pd
import requests
from api_key import api_key

app = Flask(__name__)

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
    
    # Convert to dictionary for template
    locations = stops_for_line.to_dict(orient='records')

    return render_template('map.html', locations=locations, routes=sorted_routes, selected_route=selected_route)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
