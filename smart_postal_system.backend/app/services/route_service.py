from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.route_model import Route
from app.models.branch_model import Branch
from app.schemas.route_schema import RouteCreate, RouteUpdate


class RouteService:

    @staticmethod
    def create_route(db: Session, route: RouteCreate) -> Route:
        """
        Create a new route.
        """
        # Validate that start and end branches are different
        if route.start_branch_id == route.end_branch_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start and end branches must be different."
            )

        # Check if start branch exists
        start_branch = db.query(Branch).filter(Branch.branch_id == route.start_branch_id).first()
        if not start_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start branch does not exist."
            )

        # Check if end branch exists
        end_branch = db.query(Branch).filter(Branch.branch_id == route.end_branch_id).first()
        if not end_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End branch does not exist."
            )

        # Check if route name already exists
        existing_route = db.query(Route).filter(Route.route_name == route.route_name).first()
        if existing_route:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route name already exists."
            )

        new_route = Route(**route.model_dump())

        db.add(new_route)
        db.commit()
        db.refresh(new_route)

        return new_route

    @staticmethod
    def get_all_routes(db: Session):
        """
        Return all routes.
        """
        return (
            db.query(Route)
            .order_by(Route.route_id)
            .all()
        )

    @staticmethod
    def get_route_by_id(db: Session, route_id: int) -> Route:
        """
        Get a route by ID.
        """
        route = (
            db.query(Route)
            .filter(Route.route_id == route_id)
            .first()
        )

        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found."
            )

        return route

    @staticmethod
    def update_route(
        db: Session,
        route_id: int,
        route_data: RouteUpdate,
    ) -> Route:
        """
        Update route details.
        """
        route = RouteService.get_route_by_id(db, route_id)

        update_data = route_data.model_dump(exclude_unset=True)

        if "start_branch_id" in update_data or "end_branch_id" in update_data:
            start_id = update_data.get("start_branch_id", route.start_branch_id)
            end_id = update_data.get("end_branch_id", route.end_branch_id)

            if start_id == end_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start and end branches must be different."
                )

            if "start_branch_id" in update_data:
                start_branch = db.query(Branch).filter(Branch.branch_id == start_id).first()
                if not start_branch:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Start branch does not exist."
                    )

            if "end_branch_id" in update_data:
                end_branch = db.query(Branch).filter(Branch.branch_id == end_id).first()
                if not end_branch:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="End branch does not exist."
                    )

        if "route_name" in update_data:
            existing = (
                db.query(Route)
                .filter(
                    Route.route_name == update_data["route_name"],
                    Route.route_id != route_id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Route name already exists."
                )

        for key, value in update_data.items():
            setattr(route, key, value)

        db.commit()
        db.refresh(route)

        return route

    @staticmethod
    def activate_route(
        db: Session,
        route_id: int,
    ) -> Route:
        """
        Activate a route.
        """
        route = RouteService.get_route_by_id(db, route_id)
        route.is_active = True

        db.commit()
        db.refresh(route)

        return route

    @staticmethod
    def deactivate_route(
        db: Session,
        route_id: int,
    ) -> Route:
        """
        Deactivate a route.
        """
        route = RouteService.get_route_by_id(db, route_id)
        route.is_active = False

        db.commit()
        db.refresh(route)

        return route

    @staticmethod
    def delete_route(
        db: Session,
        route_id: int,
    ):
        """
        Delete a route.
        """
        route = RouteService.get_route_by_id(db, route_id)

        db.delete(route)
        db.commit()

        return {
            "message": "Route deleted successfully."
        }
