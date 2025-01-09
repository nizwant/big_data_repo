from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import requests
from confluent_kafka import Consumer, KafkaException, KafkaError
import json
from api_key import api_key

app = Flask(__name__)

# Global variable to store the last known message
last_known_message = None

# Kafka Consumer Setup
def create_kafka_consumer():
    consumer = Consumer({
        'bootstrap.servers': 'kafka_bd:9093',  # Kafka server
        'group.id': 'flask-app-group',
        'auto.offset.reset': 'earliest',  # Always read the latest message when the consumer starts
    })
    consumer.subscribe(['transport-location'])  # Subscribe to the topic
    return consumer

# Fetch latest vehicle location from Kafka
def fetch_latest_vehicle_location_from_kafka():
    global last_known_message
    
    consumer = create_kafka_consumer()

    try:
        # Poll for a new message from Kafka (with timeout)
        msg = consumer.poll(1.0)  # Timeout after 1 second
        
        if msg is None:
            # If there are no new messages, return the last known message
            return last_known_message
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # No new messages in this partition
                return last_known_message
            else:
                raise KafkaException(msg.error())

        # Decode the message and store it as the latest known message
        latest_message = json.loads(msg.value().decode('utf-8'))
        if len(latest_message["result"]) < 100:
            return last_known_message
        last_known_message = latest_message
        return latest_message
    
    finally:
        consumer.close()

# Fetch routes from the API
url_routes = "https://api.um.warszawa.pl/api/action/public_transport_routes"
params_routes = {
    "apikey": api_key,
}
routes_response = requests.get(url_routes, params=params_routes)
routes = routes_response.json()["result"]

# Sort routes 
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

    # Get the latest vehicle location from Kafka or last known message
    latest_location = fetch_latest_vehicle_location_from_kafka()

    latest_location_df = pd.json_normalize(latest_location["result"])
    latest_location_df.rename(columns={"Lat": "Latitude", "Lon": "Longitude"}, inplace=True)
    latest_location_df["Label"] = latest_location_df["Lines"].astype(str) + "/" + latest_location_df["Brigade"].astype(str)
    latest_location_df["Latitude"] = latest_location_df["Latitude"].astype(str)
    latest_location_df["Longitude"] = latest_location_df["Longitude"].astype(str)
    latest_location_df['Time'] = pd.to_datetime(latest_location_df['Time'])
    
    # Filter out old data (within last 30 seconds)
    time_diff = datetime.now() - latest_location_df['Time']
    latest_location_df = latest_location_df[time_diff <= pd.Timedelta(seconds=30)]
    locations_for_line = latest_location_df[latest_location_df["Lines"] == selected_route]


    # Convert to dictionary for template
    stops_locations = stops_for_line.to_dict(orient='records')
    vehicle_locations = locations_for_line.to_dict(orient="records")

    return render_template('map.html', stops_locations=stops_locations, routes=sorted_routes, selected_route=selected_route, vehicle_locations=vehicle_locations)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
