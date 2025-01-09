from flask import Flask, render_template
import pandas as pd
import requests
from api_key import api_key

app = Flask(__name__)

url = "https://api.um.warszawa.pl/api/action/dbstore_get"
params = {
    "id": "ab75c33d-3a26-4342-b36a-6e5fef0a3ac3",  # resource id given by the API
    "apikey": api_key,
}
stops = requests.get(url, params=params)

url = "https://api.um.warszawa.pl//api/action/public_transport_routes"
params = {
    "apikey": api_key,
}
routes = requests.get(url, params=params)


rows = [
    {entry["key"]: entry["value"] for entry in item["values"]}
    for item in stops.json()["result"]
]
df_transport_location = pd.DataFrame(rows)
df_transport_location.rename(columns={"szer_geo": "Latitude", "dlug_geo": "Longitude"}, inplace=True)
df_transport_location["Label"] = df_transport_location["nazwa_zespolu"].astype(str) + " " + df_transport_location["slupek"].astype(str)

@app.route('/')
def index():
    # Pass the DataFrame data to the template
    locations = df_transport_location.to_dict(orient='records')  # Convert the DataFrame to a list of dictionaries
    return render_template('map.html', locations=locations)

if __name__ == '__main__':
    app.run(debug=True)