import httpx
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "https://api.openweathermap.org/geo/1.0"

async def search_cities(query: str) -> List[Dict]:
    """
    Search for cities matching a query string using OpenWeather Geocoding API.
    Returns a list of up to 5 matching locations with name, country, and state.
    """
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "q": query,
                "limit": 5,
                "appid": API_KEY
            }
            response = await client.get(f"{GEO_URL}/direct", params=params)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data:
                results.append({
                    "name": item["name"],
                    "country": item["country"],
                    "state": item.get("state", ""),
                    "lat": item["lat"],
                    "lon": item["lon"]
                })
            return results
        except Exception as e:
            print(f"Error searching cities: {e}")
    return []

async def get_coordinates(city_name: str) -> Optional[Dict]:
    """
    Calls the OpenWeather Geocoding API to get latitude and longitude for a city name.
    """
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "q": city_name,
                "limit": 1,
                "appid": API_KEY
            }
            response = await client.get(f"{GEO_URL}/direct", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return {
                    "lat": data[0]["lat"],
                    "lon": data[0]["lon"],
                    "name": data[0]["name"],
                    "country": data[0]["country"]
                }
        except Exception as e:
            print(f"Error fetching coordinates: {e}")
    return None

async def get_current_weather(lat: float, lon: float, units: str = "metric") -> Optional[Dict]:
    """
    Fetches the current weather conditions for specific coordinates.
    """
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "units": units,
                "appid": API_KEY
            }
            response = await client.get(f"{BASE_URL}/weather", params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "feels_like": data["main"]["feels_like"]
            }
        except Exception as e:
            print(f"Error fetching current weather: {e}")
    return None

async def get_forecast(lat: float, lon: float, units: str = "metric") -> List[Dict]:
    """
    Fetches the 5-day weather forecast (in 3-hour intervals) for specific coordinates.
    """
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "units": units,
                "appid": API_KEY
            }
            response = await client.get(f"{BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract 5-day forecast (OpenWeather gives 3-hour intervals)
            forecast = []
            for item in data["list"]:
                forecast.append({
                    "temp": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "timestamp": datetime.fromtimestamp(item["dt"])
                })
            return forecast
        except Exception as e:
            print(f"Error fetching forecast: {e}")
    return []
