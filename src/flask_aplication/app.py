from flask import Flask, render_template
import pandas as pd
import requests
from api_key import api_key

app = Flask(__name__)

# get all stops for a given route
url = "https://api.um.warszawa.pl//api/action/public_transport_routes"
params = {
    "apikey": api_key,
}
routes = requests.get(url, params=params)

# get all stops 
url = "https://api.um.warszawa.pl/api/action/dbstore_get"
params = {
    "id": "ab75c33d-3a26-4342-b36a-6e5fef0a3ac3",  # resource id given by the API
    "apikey": api_key,
}
stops = requests.get(url, params=params)
rows = [
    {entry["key"]: entry["value"] for entry in item["values"]}
    for item in stops.json()["result"]
]
stops_df = pd.DataFrame(rows)
stops_df.rename(columns={"szer_geo": "Latitude", "dlug_geo": "Longitude"}, inplace=True)
stops_df["Label"] = stops_df["nazwa_zespolu"].astype(str) + " " + stops_df["slupek"].astype(str)

@app.route('/')
def index():
    stops_for_line = []
    for i,j in routes.json()["result"]["159"].items():
        for k,l in j.items():
            stops_for_line.append(l)

    stops_for_line = pd.DataFrame(stops_for_line)
    stops_for_line = stops_for_line.drop(columns=["odleglosc", "ulica_id", "typ"]).drop_duplicates()
    stops_for_line = pd.merge(stops_for_line, stops_df, left_on=["nr_zespolu", "nr_przystanku"], right_on=["zespol", "slupek"], how="left")

    
    locations = stops_for_line.to_dict(orient='records')  # Convert the DataFrame to a list of dictionaries
    return render_template('map.html', locations=locations)

if __name__ == '__main__':
    app.run(debug=True)