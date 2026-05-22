import requests
import os
from datetime import datetime

API_KEY = os.environ.get("N2YO_API_KEY") # keep your real key here

def get_satellites():
    url = f"https://api.n2yo.com/rest/v1/satellite/above/48.8566/2.3522/0/90/18/&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    count = data['info']['satcount']
    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"[{timestamp}] Satellites above Paris: {count}")
    print("-" * 40)

    for sat in data['above']:
        print(f"  {sat['satname']:<25} lat: {sat['satlat']:.2f}  lng: {sat['satlng']:.2f}  alt: {sat['satalt']:.1f} km")

get_satellites()