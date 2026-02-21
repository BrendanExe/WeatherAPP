from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class Location(SQLModel, table=True):
    """
    Represents a geographical location (City) tracked by the user.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    country: str
    lat: float
    lon: float
    display_name: Optional[str] = None
    is_favorite: bool = Field(default=False)
    last_synced: Optional[datetime] = None
    
    # Relationship to snapshots
    snapshots: List["WeatherSnapshot"] = Relationship(back_populates="location")

class WeatherSnapshot(SQLModel, table=True):
    """
    A point-in-time record of weather conditions for a specific location.
    Used for local data persistence and historical tracking.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="location.id")
    temp: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    feels_like: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to location
    location: Optional[Location] = Relationship(back_populates="snapshots")

