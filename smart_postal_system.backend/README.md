# Smart Postal System API Backend

A premium, state-of-the-art FastAPI backend application designed to streamline postal logistics, parcel tracking, route planning, branch operations, and vehicle management.

---

## 🚀 Features

- **Robust Authentication**: JWT-based authentication with role-based access control (Admin, Employee, Customer).
- **Branch Management**: Create, update, activate, and deactivate branches with geo-coordinates and manager profiles.
- **Vehicle Fleet Operations**: Track vehicle availability, driver assignments, capacity limits, and statuses.
- **Parcel Booking & Tracking**: Book parcels with weight details, receiver info, source-to-destination routing, and live tracking status updates.
- **Delivery Assignments**: Assign deliveries to employees and manage workload balances.
- **Auto-generated Swagger API Docs**: Fully interactive API explorer and documentation built-in.

---

## 🛠️ Tech Stack & Prerequisites

- **Python**: Version 3.10 or higher.
- **Framework**: FastAPI (Asynchronous Web Framework).
- **Database**: SQLite (SQLAlchemy ORM for structured queries).
- **Development Server**: Uvicorn.
- **Environment**: Pydantic v2 (Validation & Settings).

---

## ⚙️ Local Setup Instructions

### 1. Clone the repository and navigate to the project directory:
```bash
cd smart_postal_system.backend
```

### 2. Set Up a Virtual Environment:
```bash
# Create a virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on Windows (CMD)
.\venv\Scripts\activate.bat

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 4. Environment Variables:
Copy `.env_example` to `.env` and fill in the configuration details.
```env
DATABASE_URL=sqlite:///./smart_postal.db
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

---

## 🏃 Running the Application

To run the FastAPI server locally in development mode:
```bash
python -m uvicorn main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## 📘 Interactive API Reference

FastAPI automatically generates interactive Swagger documentation for the API:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🗃️ DB Schema & Models Entity Relationship

- **User**: User profiles (auth credentials, full name, phone, address, and role).
- **Employee**: Employee specific attributes linked to a User, including designation, active workload status, and branch assignment.
- **Branch**: Smart postal centers containing address, contact details, coordinates, and active status.
- **Vehicle**: Logistics fleet containing capacity, status, current branch location, and driver/employee assignment.
- **Parcel**: Main booking tracking entity containing sender/receiver details, source/destination branches, expected delivery date, status, etc.
- **TrackingHistory**: Historical record logs detailing every transit update for a parcel.
- **DeliveryAssignment**: Parcel delivery task logs assigned to logistics agents.
