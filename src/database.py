from sqlmodel import create_engine, SQLModel, Session
import os

# Database config
sqlite_file_name = "weather_database.db"
sqlite_url = f"sqlite:///./{sqlite_file_name}"

# Create the SQLAlchemy engine for the SQLite database
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    """
    Creates the database file and all tables defined in the models.
    Called on application startup.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
