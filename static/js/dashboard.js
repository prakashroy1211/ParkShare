// parkshare/static/js/dashboard.js
// Helper function to get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Fetch a fresh CSRF token
async function fetchCsrfToken(tabId) {
    try {
        const response = await fetch(`/api/get-csrf-token/?tab_id=${tabId}`, {
            method: 'GET',
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error(`Failed to fetch CSRF token: ${response.status}`);
        }
        const data = await response.json();
        if (data.csrf_token) {
            document.cookie = `csrftoken=${data.csrf_token}; path=/; SameSite=Lax`;
            return data.csrf_token;
        }
        throw new Error("CSRF token not returned");
    } catch (error) {
        console.error("Error fetching CSRF token:", error);
        return null;
    }
}

// Handle logout
async function handleLogout(tabId) {
    try {
        let csrfToken = document.querySelector('#csrf-token')?.value || getCookie("csrftoken");
        const freshCsrfToken = await fetchCsrfToken(tabId);
        if (freshCsrfToken) {
            csrfToken = freshCsrfToken;
        }

        if (!csrfToken) {
            throw new Error("CSRF token missing. Please refresh the page and try again.");
        }

        const response = await fetch(`/logout/?tab_id=${tabId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            credentials: 'include'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const responseData = await response.json();
        if (responseData.message === "Logout successful") {
            if (responseData.csrf_token) {
                document.cookie = `csrftoken=${responseData.csrf_token}; path=/; SameSite=Lax`;
            }
            sessionStorage.removeItem("user");
            sessionStorage.removeItem("tab_id");
            window.location.href = `/login/?tab_id=${tabId}`;
        } else {
            throw new Error(responseData.message || "Logout failed");
        }
    } catch (error) {
        console.error("Error during logout:", error);
        alert("Error during logout: " + error.message);
    }
}

// Owner Dashboard Functions
function showEditForm(lotId) {
    document.getElementById(`edit-form-${lotId}`).style.display = 'block';
}

function hideEditForm(lotId) {
    document.getElementById(`edit-form-${lotId}`).style.display = 'none';
}

function showAddParkingLotModal() {
    document.getElementById('add-parking-lot-modal').style.display = 'flex';
}

function hideAddParkingLotModal() {
    document.getElementById('add-parking-lot-modal').style.display = 'none';
}

async function editParkingLot(lotId, tabId) {
    try {
        const formData = new FormData();
        formData.append('parking_lot_id', lotId);
        formData.append('lot_name', document.getElementById(`lot-name-${lotId}`).value);
        formData.append('vehicle_type', document.getElementById(`vehicle-type-${lotId}`).value);
        formData.append('vehicle_capacity', document.getElementById(`vehicle-capacity-${lotId}`).value);
        formData.append('price_per_hour', document.getElementById(`price_per_hour-${lotId}`).value);
        formData.append('location', document.getElementById(`location-${lotId}`).value);
        const pictureInput = document.getElementById(`picture-${lotId}`);
        if (pictureInput.files.length > 0) {
            formData.append('picture', pictureInput.files[0]);
        }

        const response = await fetch(`/api/edit-parking-lot/?tab_id=${tabId}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie("csrftoken"),
            },
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert(data.message);
            location.reload();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Edit error:', error);
        alert(`Error editing parking lot: ${error.message}`);
    }
}

async function deleteParkingLot(lotId, tabId) {
    if (!confirm('Are you sure you want to delete this parking lot?')) return;

    try {
        const response = await fetch(`/api/delete-parking-lot/?tab_id=${tabId}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken"),
            },
            body: JSON.stringify({ parking_lot_id: lotId }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert(data.message);
            location.reload();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert(`Error deleting parking lot: ${error.message}`);
    }
}

async function addParkingLot(form, tabId) {
    try {
        const formData = new FormData(form);
        const response = await fetch(`/api/add-parking-lot/?tab_id=${tabId}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie("csrftoken"),
            },
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert('Parking lot added successfully!');
            location.reload();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Add error:', error);
        alert(`Error adding parking lot: ${error.message}`);
    }
}

// User Dashboard Functions (to be expanded based on user_dashboard.html)
function searchLocation(map) {
    const searchQuery = document.getElementById('searchLocation').value;
    if (searchQuery) {
        const geocodeUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${searchQuery}`;
        
        fetch(geocodeUrl)
            .then(response => response.json())
            .then(data => {
                if (data && data.length > 0) {
                    const lat = data[0].lat;
                    const lon = data[0].lon;
                    map.setView([lat, lon], 13);
                    L.marker([lat, lon]).addTo(map)
                        .bindPopup(`${searchQuery}`)
                        .openPopup();
                } else {
                    alert("Location not found");
                }
            })
            .catch(error => {
                console.error('Error searching location:', error);
                alert("Error searching location");
            });
    }
}

function displayParkingLots(parkingLots, map) {
    const parkingSlotsContainer = document.getElementById('parkingSlots');
    parkingSlotsContainer.innerHTML = '<h3>Available Parking Lots</h3>';

    if (parkingLots.length === 0) {
        parkingSlotsContainer.innerHTML += '<p>No parking lots available.</p>';
        return;
    }

    parkingLots.forEach(lot => {
        const slotDiv = document.createElement('div');
        slotDiv.className = 'parking-slot';
        slotDiv.id = `parking-slot-${lot.id}`;
        slotDiv.innerHTML = `
            <div>
                <strong>${lot.lot_name}</strong><br>
                Location: ${lot.location}<br>
                Vehicle Type: ${lot.vehicle_type}<br>
                Capacity: <span id="capacity-${lot.id}">${lot.vehicle_capacity}</span><br>
                Price per Hour: $${lot.price_per_hour}
            </div>
            <button onclick="reserveParkingLot(${lot.id}, '${tabId}')"
                    class="${lot.vehicle_capacity > 0 ? 'available' : 'unavailable'}"
                    ${lot.vehicle_capacity <= 0 ? 'disabled' : ''}>
                Reserve
            </button>
        `;
        parkingSlotsContainer.appendChild(slotDiv);

        if (lot.location) {
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${lot.location}`)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const lat = data[0].lat;
                        const lon = data[0].lon;
                        L.marker([lat, lon]).addTo(map)
                            .bindPopup(`<b>${lot.lot_name}</b><br>${lot.location}<br>Capacity: ${lot.vehicle_capacity}`)
                            .on('click', () => map.setView([lat, lon], 13));
                    }
                })
                .catch(error => console.error(`Error geocoding ${lot.location}:`, error));
        }
    });
}

async function reserveParkingLot(parkingLotId, tabId) {
    try {
        const response = await fetch(`/api/reserve-parking-lot/?tab_id=${tabId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken"),
            },
            body: JSON.stringify({ parking_lot_id: parkingLotId }),
            credentials: 'include'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert(data.message);
            const capacityElement = document.getElementById(`capacity-${parkingLotId}`);
            if (capacityElement) {
                capacityElement.textContent = data.updated_capacity;
            }
            const button = document.querySelector(`#parking-slot-${parkingLotId} button`);
            if (button) {
                if (data.updated_capacity <= 0) {
                    button.classList.remove('available');
                    button.classList.add('unavailable');
                    button.disabled = true;
                }
            }
        } else {
            throw new Error(data.message || 'Reservation failed');
        }
    } catch (error) {
        console.error('Error reserving parking lot:', error);
        alert(`Error reserving parking lot: ${error.message}`);
    }
}