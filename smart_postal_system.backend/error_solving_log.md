# Error Solving Log

This document records the errors encountered during the implementation and verification of the **Route** module, along with their root causes and how they were solved.

---

## 1. SQLAlchemy InvalidRequestError ('Vehicle' not located)

### Error Message
```
sqlalchemy.exc.InvalidRequestError: When initializing mapper Mapper[Branch(branches)], expression 'Vehicle' failed to locate a name ('Vehicle'). If this is a class name, consider adding this relationship() to the <class 'app.models.branch_model.Branch'> class after both dependent classes have been defined.
```

### Root Cause
SQLAlchemy relationship registry requires all classes referenced in relationships (like `Vehicle` inside `Branch`) to be imported/loaded into memory so they register with the declarative base *before* any query executes. In the test verification script `verify_routes.py`, only `Branch` and `Route` were imported, leading to a registry lookup failure for other relationships like `Vehicle`.

### Solution / Solving Method
Imported all models at the top of the validation script to guarantee they are registered in SQLAlchemy before executing any queries:
```python
from app.models.user_model import User
from app.models.parcel_model import Parcel
from app.models.employee_model import Employee
from app.models.tracking_model import TrackingHistory
from app.models.branch_model import Branch
from app.models.vehicle_model import Vehicle
from app.models.route_model import Route
from app.models.delivery_assignment_model import DeliveryAssignment
```

---

## 2. UnicodeEncodeError on Windows Console

### Error Message
```
Traceback (most recent call last):
  File "D:\smart_postal_system\smart_postal_system.backend\verify_routes.py", line 188, in <module>
    print(f"\n\u274c TEST RUN ENCOUNTERED AN ERROR: {e}")
...
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 2: character maps to <undefined>
```

### Root Cause
The Windows console environment uses `cp1252` encoding by default, which cannot render certain Unicode emojis (such as ❌ `\u274c`, ✅ `\u2705`, and 🎉 `\U0001f389`).

### Solution / Solving Method
Replaced the emoji symbols in print statements with standard ASCII text alternatives:
- `❌` -> `[FAIL]`
- `✅` -> `[PASS]`
- `🎉` -> `[SUCCESS]`
- `\u274c` -> `[ERROR]`

---

## 3. SQLite OperationalError: no such column branches.branch_id

### Error Message
```
sqlite3.OperationalError: no such column: branches.branch_id
```

### Root Cause
The local pre-existing SQLite database `smart_postal.db` had a schema mismatch: the primary key column for the `branches` table was defined as `id` in the database, while the `Branch` model in `branch_model.py` maps it as `branch_id`.

### Solution / Solving Method
Instead of using the potentially out-of-sync local database file, configured the validation script to use an isolated temporary database file `test_smart_postal.db`. The script removes this file prior to running, allows SQLAlchemy to generate fresh tables matching the models, runs the validation tests, and then cleans up the temporary database file upon completion.

---

## 4. WinError 32: The process cannot access the file (test_smart_postal.db)

### Error Message
```
Could not clean up temporary DB file: [WinError 32] The process cannot access the file because it is being used by another process: 'test_smart_postal.db'
```

### Root Cause
On Windows, open file descriptors or connection pools prevent deleting a file. Simply closing the database session `db.close()` does not close all connections in the SQLAlchemy connection pool, meaning the SQLite engine still holds an open file handle to `test_smart_postal.db`.

### Solution / Solving Method
Added a call to `engine.dispose()` in the cleanup block to dispose of the connection pool and close all underlying connections before deleting the file:
```python
db.close()
engine.dispose()
os.remove(TEST_DB_FILE)
```

---

## 5. ModuleNotFoundError: No module named 'httpx'

### Error Message
```
Traceback (most recent call last):
  File "D:\smart_postal_system\smart_postal_system.backend\verify_optimization.py", line 35, in <module>
    from app.services.route_optimization_service import RouteOptimizationService
  ...
ModuleNotFoundError: No module named 'httpx'
```

### Root Cause
The `httpx` module (used by the OpenRouteService client `utils/ors_client.py`) was not installed in the current virtual environment.

### Solution / Solving Method
Ran `pip install httpx` inside the active Python virtual environment to install the missing HTTP client library.

---

## 6. FastAPI Circular Import on Global Python Installation

### Error Message
```
ImportError: cannot import name 'HTTPException' from partially initialized module 'fastapi' (most likely due to a circular import) (C:\Users\Sabari\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\fastapi\__init__.py)
```

### Root Cause
The global FastAPI package (`Lib/site-packages/fastapi`) was corrupted: the file `exceptions.py` had been overwritten with code from `utils/ors_client.py` containing a class definition for `ORSClient` and importing `fastapi` again, causing a circular import when trying to start FastAPI.

### Solution / Solving Method
Copied the clean, uncorrupted `exceptions.py` file from the virtual environment site-packages (`venv/Lib/site-packages/fastapi/exceptions.py`) back to the global site-packages path to restore FastAPI to its original state.

---

## 7. Postgresql OperationalError: host name not resolved

### Error Message
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not translate host name "ep-steep-cell-atnqmo4i.c-9.us-east-1.aws.neon.tech" to address: Name or service not known
```

### Root Cause
The `.env` file lists `DATABASE_URL` as a remote PostgreSQL Neon database. When the server is started in a sandbox or environment without network access to Neon, hostname resolution fails.

### Solution / Solving Method
Changed the `DATABASE_URL` in `.env` (or override it in the run configuration) to point to the local SQLite database file `sqlite:///./smart_postal.db`.

---

## 8. WinError 10013: Socket access permission forbidden

### Error Message
```
ERROR:    [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
```

### Root Cause
This error occurs when attempting to bind to a port (like the default `8000`) that is either:
- Excluded or reserved by Windows (for example, by Hyper-V or Windows NAT/WSL port exclusion ranges).
- Used by another local process running under a different privilege level (e.g. system service or admin-privileged application).

### Solution / Solving Method
The simplest and most reliable resolution is to run the uvicorn development server on a different port, such as `8001`, `8080`, or `5000`:
```bash
python -m uvicorn main:app --port 8001 --reload
```

---

## 9. SQLAlchemy Warning: DeliveryAssignment assigned_user relationship overlap

### Error Message
```
SAWarning: relationship 'DeliveryAssignment.assigned_user' will copy column users.user_id to column delivery_assignments.assigned_by, which conflicts with relationship(s): 'User.delivery_assignments' (copies users.user_id to delivery_assignments.assigned_by).
```

### Root Cause
SQLAlchemy detected two independent one-way relationships (`User.delivery_assignments` and `DeliveryAssignment.assigned_user`) targeting the same foreign key field (`delivery_assignments.assigned_by`). Because they were not explicitly linked, SQLAlchemy warned that updates to one relationship would not automatically synchronize with the other.

### Solution / Solving Method
Connected the relationships bidirectionally by adding the `back_populates` parameter:
* In `app/models/user_model.py`:
  ```python
  delivery_assignments = relationship(
      "DeliveryAssignment",
      foreign_keys="DeliveryAssignment.assigned_by",
      back_populates="assigned_user"
  )
  ```
* In `app/models/delivery_assignment_model.py`:
  ```python
  assigned_user = relationship(
      "User",
      foreign_keys=[assigned_by],
      back_populates="delivery_assignments"
  )
  ```




