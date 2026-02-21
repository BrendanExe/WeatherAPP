# SkyCast | Weather Data Integration Platform

SkyCast is a modern, full-stack weather management application that integrates with the OpenWeatherMap API. Users can track multiple cities, view real-time weather data and 5-day forecasts, and manage their watchlist with a premium glassy user interface.

## 🚀 Features

- **Real-time Integration:** Fetches current weather and 5-day forecasts via OpenWeatherMap.
- **Local Persistence:** Uses SQLite and SQLModel to store locations, historical snapshots, and user preferences.
- **Full CRUD:** Add, view, favorite, and remove cities from your watchlist.
- **Data Synchronization:** Manual sync for all tracked locations with timestamp tracking.
- **Premium UI:** Responsive, Glassmorphism-based design with Lucide icons and subtle animations.
- **Error Handling:** Graceful handling of invalid cities and API failures.

## 🛠 Tech Stack

- **Backend:** FastAPI (Python 3.14)
- **Database:** SQLite with SQLModel (SQLAlchemy + Pydantic)
- **Frontend:** Vanilla HTML5, CSS3 (Modern Variables & Glassmorphism), ES6+ JavaScript
- **API Client:** `httpx` for asynchronous requests

## 📦 Setup Instructions

1. **Clone the project** (or navigate to the project directory).
2. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn sqlmodel httpx python-dotenv
   ```
3. **Configure API Key**:
   - Create a `.env` file in the root directory (one has been provided as a template).
   - Add your OpenWeatherMap API key:
     ```env
     OPENWEATHER_API_KEY=your_actual_api_key_here
     ```
   - *Note: You can get a free key at [openweathermap.org](https://openweathermap.org/api).*

4. **Run the Application**:
   ```bash
   python main.py
   ```
   The application will be available at `http://localhost:8000`.

## 🏗 Architectural Decisions

- **FastAPI:** Chosen for its high performance, native async support, and automatic documentation (available at `/docs`).
- **SQLModel:** Combines the power of SQLAlchemy with Pydantic's data validation, making it perfect for relational data in a modern Python stack.
- **Vanilla Frontend:** For a fast, lightweight, and framework-independent experience that demonstrates core DOM manipulation and styling skills.
- **Snapshot Pattern:** Instead of just storing the current weather in the Location table, we use a `WeatherSnapshot` table. This allows for historical data tracking and "conflict" checks.

## 🧠 Assumptions & Considerations

1. **API Key:** It is assumed the user will provide a valid "Free Tier" API key.
2. **Units:** Default units are set to Metric (°C, m/s). This can be extended via the `UserPreference` table.
3. **Conflict Handling:** Implemented a log-based warning if temperature shifts significantly (>10°C) between syncs, simulating a check for anomalous data.
4. **Geocoding:** The app uses the Geocoding API to resolve city names to coordinates before fetching weather data, ensuring higher accuracy.

## 🧪 Testing

A basic test suite is included in `tests/test_api.py`. Run tests using:
```bash
pytest
```
