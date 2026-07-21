from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import role_required
from app.models.user_model import User
from app.schemas.dashboard_schema import DashboardResponse
from app.services.dashboard_service import get_dashboard_data

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"]))
):
    """
    Returns aggregated dashboard statistics for the admin panel.

    Includes:
    - Overview counts (parcels, users, employees, branches, vehicles, assignments)
    - Parcel status breakdown
    - Employee availability stats
    - Vehicle status stats
    - Branch active/inactive stats
    - Delivery assignment status stats
    - Recent parcels (last 10)
    - Recent tracking activity (last 10)
    - Top 5 performing employees by completed deliveries
    - Parcel priority breakdown
    """
    return get_dashboard_data(db)
