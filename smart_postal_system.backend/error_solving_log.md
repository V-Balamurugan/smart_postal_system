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
