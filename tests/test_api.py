import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from src.main import app, get_db
from src.models import Location

# Setup file-based SQLite for testing
sqlite_url = "sqlite:///test.db"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
)

def override_get_db():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_create_location_success(session: Session):
    # Mocking weather_api calls
    mock_geo = {
        "name": "London",
        "country": "GB",
        "lat": 51.5074,
        "lon": -0.1278
    }
    mock_weather = {
        "temp": 15.5,
        "description": "clear sky",
        "icon": "01d",
        "humidity": 50,
        "wind_speed": 5.0,
        "feels_like": 14.0
    }
    
    with patch("src.weather_api.get_coordinates", new_callable=AsyncMock) as mock_coords, \
         patch("src.weather_api.get_current_weather", new_callable=AsyncMock) as mock_curr:
        
        mock_coords.return_value = mock_geo
        mock_curr.return_value = mock_weather
        
        response = client.post("/api/locations?city_name=London")
        
        assert response.status_code == 200
        data = response.json()
        print(f"DEBUG: Response data: {data}")
        assert data["name"] == "London"
        assert data["country"] == "GB"
        
        # Verify it exists in DB
        location = session.exec(select(Location).where(Location.name == "London")).first()
        assert location is not None
        assert location.lat == 51.5074

def test_read_locations_after_creation(session: Session):
    # Setup some data
    loc = Location(name="Paris", country="FR", lat=48.8566, lon=2.3522)
    session.add(loc)
    session.commit()
    
    response = client.get("/api/locations")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Paris"
