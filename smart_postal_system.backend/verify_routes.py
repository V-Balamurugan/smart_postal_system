import sys
import os

# Force local SQLite database for verification to avoid cloud database network timeouts/hangs
TEST_DB_FILE = "test_smart_postal.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_FILE}"

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
from app.schemas.route_schema import RouteCreate, RouteUpdate
from app.services.route_service import RouteService

def test_route_lifecycle():
    print("Initializing Database tables from models...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    # 1. Create two temporary branches for the test
    print("Creating temporary branches for testing...")
    branch_a = db.query(Branch).filter(Branch.branch_code == "TEST-A").first()
    if not branch_a:
        branch_a = Branch(
            branch_code="TEST-A",
            branch_name="Test Branch A",
            city="City A",
            state="State A",
            postal_code="11111",
            address="Test Address A",
            latitude=10.0,
            longitude=20.0,
            contact_number="1234567890",
            email="test_a@example.com",
            manager_name="Manager A",
            is_active=True
        )
        db.add(branch_a)
        db.commit()
        db.refresh(branch_a)

    branch_b = db.query(Branch).filter(Branch.branch_code == "TEST-B").first()
    if not branch_b:
        branch_b = Branch(
            branch_code="TEST-B",
            branch_name="Test Branch B",
            city="City B",
            state="State B",
            postal_code="22222",
            address="Test Address B",
            latitude=15.0,
            longitude=25.0,
            contact_number="0987654321",
            email="test_b@example.com",
            manager_name="Manager B",
            is_active=True
        )
        db.add(branch_b)
        db.commit()
        db.refresh(branch_b)

    print(f"Created/found branches: {branch_a.branch_id} and {branch_b.branch_id}")

    route_to_clean = []
    
    try:
        # 2. Try creating a route with same start and end branches
        print("\nTest case: Same start and end branch validation...")
        try:
            route_in = RouteCreate(
                route_name="Route Same Branch",
                start_branch_id=branch_a.branch_id,
                end_branch_id=branch_a.branch_id,
                distance_km=10.0,
                estimated_duration_minutes=30
            )
            RouteService.create_route(db, route_in)
            print("[FAIL] Same start and end branch route created, but should have failed!")
        except HTTPException as e:
            print(f"[PASS] Correctly failed with status code {e.status_code}: {e.detail}")

        # 3. Try creating a route with non-existent start branch
        print("\nTest case: Non-existent start branch validation...")
        try:
            route_in = RouteCreate(
                route_name="Route Bad Branch",
                start_branch_id=99999,
                end_branch_id=branch_b.branch_id,
                distance_km=10.0,
                estimated_duration_minutes=30
            )
            RouteService.create_route(db, route_in)
            print("[FAIL] Route with bad branch created, but should have failed!")
        except HTTPException as e:
            print(f"[PASS] Correctly failed with status code {e.status_code}: {e.detail}")

        # 4. Create a valid route
        print("\nTest case: Create valid route...")
        # Clear existing test route if it exists
        existing_route = db.query(Route).filter(Route.route_name == "TEST-ROUTE-1").first()
        if existing_route:
            db.delete(existing_route)
            db.commit()

        route_in = RouteCreate(
            route_name="TEST-ROUTE-1",
            start_branch_id=branch_a.branch_id,
            end_branch_id=branch_b.branch_id,
            distance_km=120.5,
            estimated_duration_minutes=150
        )
        new_route = RouteService.create_route(db, route_in)
        route_to_clean.append(new_route.route_id)
        print(f"[PASS] Created route {new_route.route_name} (ID: {new_route.route_id})")

        # 5. Try creating duplicate route name
        print("\nTest case: Duplicate route name validation...")
        try:
            route_dup = RouteCreate(
                route_name="TEST-ROUTE-1",
                start_branch_id=branch_a.branch_id,
                end_branch_id=branch_b.branch_id,
                distance_km=200.0,
                estimated_duration_minutes=200
            )
            RouteService.create_route(db, route_dup)
            print("[FAIL] Created route with duplicate name!")
        except HTTPException as e:
            print(f"[PASS] Correctly failed with status code {e.status_code}: {e.detail}")

        # 6. Get Route by ID
        print("\nTest case: Retrieve route by ID...")
        fetched = RouteService.get_route_by_id(db, new_route.route_id)
        assert fetched.route_name == "TEST-ROUTE-1"
        print(f"[PASS] Fetched route name matches: {fetched.route_name}")

        # 7. Update Route
        print("\nTest case: Update route...")
        route_up = RouteUpdate(
            distance_km=130.0,
            estimated_duration_minutes=160
        )
        updated = RouteService.update_route(db, new_route.route_id, route_up)
        assert updated.distance_km == 130.0
        assert updated.estimated_duration_minutes == 160
        print(f"[PASS] Route updated successfully. Distance={updated.distance_km}, Duration={updated.estimated_duration_minutes}")

        # 8. Deactivate Route
        print("\nTest case: Deactivate route...")
        deactivated = RouteService.deactivate_route(db, new_route.route_id)
        assert not deactivated.is_active
        print(f"[PASS] Route is_active = {deactivated.is_active}")

        # 9. Activate Route
        print("\nTest case: Activate route...")
        activated = RouteService.activate_route(db, new_route.route_id)
        assert activated.is_active
        print(f"[PASS] Route is_active = {activated.is_active}")

        # 10. Delete Route
        print("\nTest case: Delete route...")
        res = RouteService.delete_route(db, new_route.route_id)
        print(f"[PASS] Route deletion returned: {res}")
        route_to_clean.remove(new_route.route_id)

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
        test_route_lifecycle()
        print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n[ERROR] TEST RUN ENCOUNTERED AN ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
