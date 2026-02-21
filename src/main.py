from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import os
from contextlib import asynccontextmanager

from .database import engine, create_db_and_tables, get_session
from .models import Location, WeatherSnapshot
from . import weather_api
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    In this case, it ensures the database and tables are created on startup.
    """
    create_db_and_tables()
    yield

app = FastAPI(title="Weather Data Integration Platform", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Dependency for database session
def get_db():
    with Session(engine) as session:
        yield session

@app.get("/api/locations", response_model=List[Location])
def read_locations(session: Session = Depends(get_db)):
    """
    Retrieve all tracked locations from the database.
    """
    locations = session.exec(select(Location)).all()
    return locations

@app.get("/api/search")
async def search_cities(q: str):
    """
    Search for cities matching a query string using the Geocoding API.
    Returns a list of up to 5 matching locations.
    """
    if not q or len(q) < 3:
        return []
    
    suggestions = await weather_api.search_cities(q)
    return suggestions

@app.post("/api/locations", response_model=Location)
async def create_location(city_name: str, session: Session = Depends(get_db)):
    """
    Add a new city to the watchlist.
    Steps:
    1. Resolve city name to coordinates using the Geocoding API.
    2. Check if the city already exists in our local DB.
    3. Save the new location and trigger an initial weather sync.
    """
    # 1. Get coords from API
    geo_data = await weather_api.get_coordinates(city_name)
    if not geo_data:
        raise HTTPException(status_code=404, detail="City not found or API error")
    
    # Check if city already exists (prevent duplicates by lat/lon)
    existing = session.exec(select(Location).where(Location.lat == geo_data["lat"], Location.lon == geo_data["lon"])).first()
    if existing:
        return existing

    # 2. Save to DB
    location = Location(
        name=geo_data["name"],
        country=geo_data["country"],
        lat=geo_data["lat"],
        lon=geo_data["lon"]
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    
    # 3. Initial sync to fetch weather data immediately
    await sync_location_weather(location.id, session)
    
    return location

@app.patch("/api/locations/{location_id}", response_model=Location)
def update_location(location_id: int, is_favorite: Optional[bool] = None, display_name: Optional[str] = None, session: Session = Depends(get_db)):
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if is_favorite is not None:
        location.is_favorite = is_favorite
    if display_name is not None:
        location.display_name = display_name
        
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

@app.delete("/api/locations/{location_id}")
def delete_location(location_id: int, session: Session = Depends(get_db)):
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Delete snapshots first (or let CASCADE handle it if configured, but SQLModel default is manual)
    snapshots = session.exec(select(WeatherSnapshot).where(WeatherSnapshot.location_id == location_id)).all()
    for s in snapshots:
        session.delete(s)
        
    session.delete(location)
    session.commit()
    return {"ok": True}

@app.get("/api/weather/{location_id}")
async def get_weather(location_id: int, session: Session = Depends(get_db)):
    """
    Get the weather data for a specific location.
    Returns the latest stored snapshot (Current) and the live 5-day forecast.
    """
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Get latest snapshot from processed local DB
    latest_snapshot = session.exec(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.location_id == location_id)
        .order_by(WeatherSnapshot.timestamp.desc())
    ).first()
    
    # Fetch live 5-day forecast from API
    forecast = await weather_api.get_forecast(location.lat, location.lon)
    
    return {
        "location": location,
        "current": latest_snapshot,
        "forecast": forecast
    }

@app.post("/api/sync/{location_id}")
async def sync_location_weather(location_id: int, session: Session = Depends(get_db)):
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Fetch from API
    weather_data = await weather_api.get_current_weather(location.lat, location.lon)
    if not weather_data:
        raise HTTPException(status_code=503, detail="Weather API unavailable")
    
    # Save snapshot
    snapshot = WeatherSnapshot(
        location_id=location_id,
        temp=weather_data["temp"],
        description=weather_data["description"],
        icon=weather_data["icon"],
        humidity=weather_data["humidity"],
        wind_speed=weather_data["wind_speed"],
        feels_like=weather_data["feels_like"]
    )
    session.add(snapshot)
    
    # Update location timestamp
    location.last_synced = datetime.utcnow()
    session.add(location)
    
    session.commit()
    return {"status": "success", "data": snapshot}

@app.get("/")
def read_root():
    # Redirect to static index.html or just serve it
    from fastapi.responses import FileResponse
    return FileResponse("src/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
