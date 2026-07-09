import sys
import os
import asyncio

# Force local SQLite database for verification to avoid cloud database network timeouts/hangs
TEST_DB_FILE = "test_smart_postal_opt.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_FILE}"
os.environ["ORS_API_KEY"] = "mock_key_for_testing"

# Delete existing test DB file to start fresh
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception as e:
        print(f"Could not remove existing test DB file: {e}")

from sqlalchemy.orm import Session
from fastapi import HTTPException

# Configure path so we can import app modules directly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import all models so SQLAlchemy registers them and avoids mapper errors
from app.models.user_model import User
from app.models.parcel_model import Parcel
from app.models.employee_model import Employee
from app.models.tracking_model import TrackingHistory
from app.models.branch_model import Branch
from app.models.vehicle_model import Vehicle
from app.models.route_model import Route
from app.models.delivery_assignment_model import DeliveryAssignment

from app.database.database import Base, engine, SessionLocal
from app.schemas.route_optimization_schema import RouteOptimizationRequest
from app.services.route_optimization_service import RouteOptimizationService
from utils.ors_client import ors_client

# Monkeypatch the get_driving_route method of the ors_client to mock external API response
async def mock_get_driving_route(start_longitude, start_latitude, end_longitude, end_latitude):
    print(f"[MOCK] intercepted ORS call from ({start_longitude}, {start_latitude}) to ({end_longitude}, {end_latitude})")
    return {
        "routes": [
            {
                "summary": {
                    "distance": 451230.5, # 451.23 km
                    "duration": 28320.0   # 472 minutes
                },
                "geometry": "encoded_polyline_mock_data_geojson_path_here"
            }
        ]
    }

ors_client.get_driving_route = mock_get_driving_route

async def test_route_optimization():
    print("Initializing Database tables from models...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    # 1. Create two temporary branches for the test (Madurai to Chennai coords)
    print("Creating temporary branches with coordinates...")
    branch_a = Branch(
        branch_code="MDU-01",
        branch_name="Madurai Central",
        city="Madurai",
        state="Tamil Nadu",
        postal_code="625001",
        address="Test Address A",
        latitude=9.9252,
        longitude=78.1198,
        contact_number="1234567890",
        email="mdu@example.com",
        manager_name="Manager A",
        is_active=True
    )
    db.add(branch_a)
    db.commit()
    db.refresh(branch_a)

    branch_b = Branch(
        branch_code="CHN-01",
        branch_name="Chennai Central",
        city="Chennai",
        state="Tamil Nadu",
        postal_code="600001",
        address="Test Address B",
        latitude=13.0827,
        longitude=80.2707,
        contact_number="0987654321",
        email="chn@example.com",
        manager_name="Manager B",
        is_active=True
    )
    db.add(branch_b)
    db.commit()
    db.refresh(branch_b)

    print(f"Created branches: {branch_a.branch_id} ({branch_a.branch_code}) and {branch_b.branch_id} ({branch_b.branch_code})")

    # 2. Create route with dummy initial values
    print("Creating initial route...")
    route = Route(
        route_name="MDU-CHN-EXP",
        start_branch_id=branch_a.branch_id,
        end_branch_id=branch_b.branch_id,
        distance_km=10.0,
        estimated_duration_minutes=10,
        is_active=True
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    print(f"Created route {route.route_name} with initial distance={route.distance_km}km, duration={route.estimated_duration_minutes}m")

    try:
        # 3. Call RouteOptimizationService
        print("\nTest case: Running route optimization...")
        request = RouteOptimizationRequest(route_id=route.route_id)
        response_data = await RouteOptimizationService.optimize_route(db, request)
        
        # 4. Assert response values
        print(f"Response returned: {response_data}")
        assert response_data["route_id"] == route.route_id
        assert response_data["distance_km"] == 451.23
        assert response_data["estimated_duration_minutes"] == 472
        assert response_data["route_geometry"] == "encoded_polyline_mock_data_geojson_path_here"
        assert response_data["optimization_status"] == "SUCCESS"
        print("[PASS] Response assertions passed!")

        # 5. Assert DB updates
        print("\nTest case: Checking database updates...")
        db.refresh(route)
        print(f"Updated DB route values: distance={route.distance_km}km, duration={route.estimated_duration_minutes}m")
        assert route.distance_km == 451.23
        assert route.estimated_duration_minutes == 472
        print("[PASS] Database assertions passed!")

    finally:
        print("\nCleaning up database connection and file...")
        db.close()
        try:
            # Dispose engine connection pool to release file handles on Windows
            engine.dispose()
            # Clean up the test database file
            if os.path.exists(TEST_DB_FILE):
                os.remove(TEST_DB_FILE)
            print("Cleanup completed successfully!")
        except Exception as e:
            print(f"Could not clean up temporary DB file: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_route_optimization())
        print("\n[SUCCESS] ALL ROUTE OPTIMIZATION TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n[ERROR] TEST RUN ENCOUNTERED AN ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
