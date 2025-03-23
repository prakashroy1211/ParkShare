## ParkShare

**ParkShare** is a web application that connects parking lot owners with drivers seeking parking spaces. Owners can list their parking lots, and drivers can reserve slots based on vehicle type, location, and price. The platform supports user roles (drivers and owners), vehicle management, reservation tracking, and a map-based interface for locating parking lots.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Deployment on AWS](#deployment-on-aws)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **User Roles**:
  - **Drivers**: Search and reserve parking slots, manage vehicles, view and cancel reservations.
  - **Owners**: Add, edit, and delete parking lots, and view reservations for their lots.
- **Vehicle Management**: Drivers can add multiple vehicles (e.g., cars, bikes, trucks) and select one when reserving a slot.
- **Parking Lot Management**: Owners can list parking lots with details like name, vehicle type, capacity, price per hour, location, and an optional picture.
- **Reservations**: Drivers can reserve parking slots, view their reservations, and cancel active ones.
- **Role-Based Access**: Users can have multiple roles (driver, owner) and switch between them using a tabbed interface.
- **Geolocation**: Parking lot locations are displayed on a map using OpenStreetMap and Leaflet.js.
- **Responsive Design**: Built with Bootstrap for a mobile-friendly experience.

## Tech Stack

- **Backend**:
  - Django 4.2 (Python 3.12)
  - Django REST Framework 3.14.0 (for API endpoints)
  - PostgreSQL (database)
- **Frontend**:
  - HTML, CSS, JavaScript
  - Bootstrap 4.5.2
  - Leaflet.js (for maps)
  - jQuery 3.5.1 (for AJAX requests)
- **Other Tools**:
  - Git (version control)
  - Virtualenv (Python environment management)
  - Gunicorn (production server, optional)
  - Nginx (reverse proxy, optional)

## Installation

Follow these steps to set up ParkShare on your local machine.

### Prerequisites

- Python 3.12
- PostgreSQL
- Git
- Virtualenv (recommended)

### Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-username/parkshare.git
   cd parkshare
2. **Set Up a Virtual Environment**:

   ```bash
   python -m venv psvenv
   source psvenv/bin/activate  # On Windows: psvenv\Scripts\activate
3. **Install Dependencies**:
  <br/>Create a requirements.txt file with the following content:
   ```bash
   django==4.2
   djangorestframework==3.14.0
   psycopg2-binary==2.9.6
Then install the dependencies:
```bash
pip install -r requirements.txt
