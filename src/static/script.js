document.addEventListener('DOMContentLoaded', () => {
    const locationGrid = document.getElementById('locationGrid');
    const cityInput = document.getElementById('cityInput');
    const addCityBtn = document.getElementById('addCityBtn');
    const syncAllBtn = document.getElementById('syncAllBtn');
    const forecastSection = document.getElementById('forecastSection');
    const closeForecast = document.getElementById('closeForecast');
    const toast = document.getElementById('toast');
    const citySuggestions = document.getElementById('citySuggestions');

    // State
    let locations = [];
    let searchTimeout = null;

    // Initialize Lucide icons (used for premium vector icons throughout the app)
    const renderIcons = () => lucide.createIcons();

    // Helper to get full country name from code (e.g., 'GB' -> 'United Kingdom')
    const regionNames = new Intl.DisplayNames(['en'], { type: 'region' });
    const getCountryName = (code) => {
        try {
            return regionNames.of(code) || code;
        } catch (e) {
            return code;
        }
    };

    /**
     * Fetch all tracked locations from the backend and trigger re-render.
     */
    async function fetchLocations() {
        try {
            const res = await fetch('/api/locations');
            locations = await res.json();
            renderLocations();
        } catch (err) {
            showToast('Failed to load locations', 'error');
        }
    }

    /**
     * Clear and re-populate the location grid with city cards.
     */
    function renderLocations() {
        locationGrid.innerHTML = '';
        if (locations.length === 0) {
            locationGrid.innerHTML = '<div class="loading">No cities tracked. Add one above!</div>';
            return;
        }

        locations.forEach(async (loc) => {
            const card = document.createElement('div');
            card.className = 'location-card';
            card.dataset.id = loc.id;
            card.innerHTML = `
                <div class="card-header">
                    <div class="city-info">
                        <h3>${loc.display_name || loc.name}</h3>
                        <p>${getCountryName(loc.country)}</p>
                    </div>
                    <div class="card-actions">
                        <button class="favorite ${loc.is_favorite ? 'active' : ''}" data-id="${loc.id}">
                            <i data-lucide="star"></i>
                        </button>
                        <button class="delete" data-id="${loc.id}">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </div>
                <div class="weather-content" id="weather-${loc.id}">
                    <div class="loading">Loading weather...</div>
                </div>
                <div class="sync-info">
                    Synced: ${loc.last_synced ? new Date(loc.last_synced).toLocaleTimeString() : 'Never'}
                </div>
            `;

            // Add click event for forecast
            card.addEventListener('click', (e) => {
                if (!e.target.closest('button')) {
                    showForecast(loc.id);
                }
            });

            locationGrid.appendChild(card);
            loadWeatherData(loc.id);
        });
        renderIcons();
    }

    /**
     * Load the current weather data snapshot for a specific card.
     * This separates the list rendering from individual weather data fetching.
     */
    async function loadWeatherData(id) {
        const container = document.getElementById(`weather-${id}`);
        try {
            const res = await fetch(`/api/weather/${id}`);
            const data = await res.json();
            const current = data.current;

            if (!current) {
                container.innerHTML = '<div class="loading">No data found. Syncing...</div>';
                return;
            }

            container.innerHTML = `
                <div class="weather-main">
                    <div class="temp-large">${Math.round(current.temp)}°</div>
                    <div class="weather-desc">
                        <img src="https://openweathermap.org/img/wn/${current.icon}@2x.png" alt="${current.description}">
                        <p>${current.description}</p>
                    </div>
                </div>
                <div class="weather-details">
                    <div class="detail-item">
                        <i data-lucide="droplets"></i>
                        <span>${current.humidity}%</span>
                    </div>
                    <div class="detail-item">
                        <i data-lucide="wind"></i>
                        <span>${current.wind_speed} m/s</span>
                    </div>
                </div>
            `;
            renderIcons();
        } catch (err) {
            container.innerHTML = '<div class="loading">Error loading weather</div>';
        }
    }

    /**
     * Fetch and display the 5-day forecast in a modal overlay.
     */
    async function showForecast(id) {
        try {
            const res = await fetch(`/api/weather/${id}`);
            const data = await res.json();
            const { location, forecast } = data;

            document.getElementById('forecastCityName').textContent = location.name;
            document.getElementById('forecastCountry').textContent = getCountryName(location.country);

            const grid = document.getElementById('forecastGrid');
            grid.innerHTML = '';

            forecast.forEach(item => {
                const date = new Date(item.timestamp);
                const itemEl = document.createElement('div');
                itemEl.className = 'forecast-item';
                itemEl.innerHTML = `
                    <div class="date">${date.toLocaleDateString(undefined, { weekday: 'short' })}</div>
                    <div class="time">${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    <img src="https://openweathermap.org/img/wn/${item.icon}.png" alt="${item.description}">
                    <div class="temp">${Math.round(item.temp)}°</div>
                    <div class="date" style="font-size: 0.6rem; margin-top: 0.5rem">${item.description}</div>
                `;
                grid.appendChild(itemEl);
            });

            forecastSection.classList.remove('hidden');
        } catch (err) {
            showToast('Error loading forecast', 'error');
        }
    }

    /**
     * Fetch city suggestions from the backend based on user input.
     */
    async function handleSearch(query) {
        if (query.length < 3) {
            citySuggestions.classList.add('hidden');
            return;
        }

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const suggestions = await res.json();

            if (suggestions.length === 0) {
                citySuggestions.classList.add('hidden');
                return;
            }

            citySuggestions.innerHTML = suggestions.map(s => `
                <div class="suggestion-item" data-name="${s.name}, ${s.country}">
                    <div class="name">${s.name}</div>
                    <div class="sub">${s.state ? s.state + ', ' : ''}${getCountryName(s.country)}</div>
                </div>
            `).join('');

            citySuggestions.classList.remove('hidden');
        } catch (err) {
            console.error('Search error:', err);
        }
    }

    // Handle selection from dropdown
    citySuggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (item) {
            cityInput.value = item.dataset.name;
            citySuggestions.classList.add('hidden');
            addCity();
        }
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.input-group')) {
            citySuggestions.classList.add('hidden');
        }
    });

    // Add City
    async function addCity() {
        const cityName = cityInput.value.trim();
        if (!cityName) return;

        addCityBtn.disabled = true;
        addCityBtn.innerHTML = '<i data-lucide="loader"></i> Adding...';
        renderIcons();

        try {
            const res = await fetch(`/api/locations?city_name=${encodeURIComponent(cityName)}`, {
                method: 'POST'
            });
            if (!res.ok) throw new Error('City not found');
            cityInput.value = '';
            showToast('City added successfully!');
            fetchLocations();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            addCityBtn.disabled = false;
            addCityBtn.innerHTML = '<i data-lucide="plus"></i> Add';
            renderIcons();
        }
    }

    // Toggle Favorite & Delete
    locationGrid.addEventListener('click', async (e) => {
        const favBtn = e.target.closest('.favorite');
        if (favBtn) {
            const id = parseInt(favBtn.dataset.id);
            const isActive = favBtn.classList.contains('active');
            try {
                const res = await fetch(`/api/locations/${id}?is_favorite=${!isActive}`, { method: 'PATCH' });
                if (res.ok) {
                    favBtn.classList.toggle('active');
                    // Update local state in memory
                    const loc = locations.find(l => l.id === id);
                    if (loc) loc.is_favorite = !isActive;
                }
            } catch (err) {
                showToast('Update failed', 'error');
            }
        }

        const delBtn = e.target.closest('.delete');
        if (delBtn) {
            e.preventDefault();
            e.stopPropagation();
            const id = Number(delBtn.dataset.id);
            if (confirm('Remove this city?')) {
                try {
                    const res = await fetch(`/api/locations/${id}`, { method: 'DELETE' });
                    if (res.ok) {
                        // Remove from DOM
                        const card = delBtn.closest('.location-card');
                        if (card) card.remove();

                        // Update local state
                        locations = locations.filter(l => l.id !== id);

                        // Show empty state if needed
                        if (locations.length === 0) {
                            renderLocations();
                        }
                        showToast('Location removed');
                    }
                } catch (err) {
                    showToast('Delete failed', 'error');
                }
            }
        }
    });

    // Refresh all
    syncAllBtn.addEventListener('click', async () => {
        syncAllBtn.classList.add('spinning');
        showToast('Syncing all cities...');

        const syncPromises = locations.map(loc =>
            fetch(`/api/sync/${loc.id}`, { method: 'POST' })
        );

        try {
            await Promise.all(syncPromises);
            showToast('All cities synced!');
            fetchLocations();
        } catch (err) {
            showToast('Some syncs failed', 'error');
        } finally {
            syncAllBtn.classList.remove('spinning');
        }
    });

    // Close Forecast
    closeForecast.addEventListener('click', () => {
        forecastSection.classList.add('hidden');
    });

    // Toast Notification
    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    // Event Listeners
    addCityBtn.addEventListener('click', addCity);

    cityInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => handleSearch(e.target.value.trim()), 300);
    });

    cityInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            citySuggestions.classList.add('hidden');
            addCity();
        }
    });

    // Initial Load
    fetchLocations();
});
