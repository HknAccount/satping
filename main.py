import requests
import os
import time
from datetime import datetime
from prometheus_client import start_http_server, Gauge

API_KEY = os.environ.get("N2YO_API_KEY")

# Prometheus metrics
satellites_above = Gauge('satellites_above_paris', 'Number of satellites above Paris')

def get_satellites():
    url = f"https://api.n2yo.com/rest/v1/satellite/above/48.8566/2.3522/0/90/18/&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    count = data['info']['satcount']
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Update Prometheus metric
    satellites_above.set(count)

    print(f"[{timestamp}] Satellites above Paris: {count}")
    print("-" * 40)

    for sat in data['above']:
        print(f"  {sat['satname']:<25} lat: {sat['satlat']:.2f}  lng: {sat['satlng']:.2f}  alt: {sat['satalt']:.1f} km")

# Start Prometheus metrics server on port 8000
start_http_server(8000)
print("Metrics available at http://localhost:8000")

# Run forever
while True:
    get_satellites()
    print("Next update in 60 seconds...\n")
    time.sleep(60)