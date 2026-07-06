from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.branch_model import Branch
from app.schemas.branch_schema import BranchCreate, BranchUpdate


class BranchService:

    @staticmethod
    def create_branch(db: Session, branch: BranchCreate) -> Branch:
        """
        Create a new branch.
        """

        existing_code = (
            db.query(Branch)
            .filter(Branch.branch_code == branch.branch_code)
            .first()
        )

        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch code already exists."
            )

        existing_email = (
            db.query(Branch)
            .filter(Branch.email == branch.email)
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch email already exists."
            )

        new_branch = Branch(**branch.model_dump())

        db.add(new_branch)
        db.commit()
        db.refresh(new_branch)

        return new_branch

    @staticmethod
    def get_all_branches(db: Session):
        """
        Return all branches.
        """

        return (
            db.query(Branch)
            .order_by(Branch.id)
            .all()
        )

    @staticmethod
    def get_branch_by_id(db: Session, branch_id: int) -> Branch:
        """
        Get a branch by ID.
        """

        branch = (
            db.query(Branch)
            .filter(Branch.id == branch_id)
            .first()
        )

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found."
            )

        return branch

    @staticmethod
    def update_branch(
        db: Session,
        branch_id: int,
        branch_data: BranchUpdate,
    ) -> Branch:
        """
        Update branch details.
        """

        branch = BranchService.get_branch_by_id(db, branch_id)

        update_data = branch_data.model_dump(exclude_unset=True)

        if "branch_code" in update_data:
            existing = (
                db.query(Branch)
                .filter(
                    Branch.branch_code == update_data["branch_code"],
                    Branch.id != branch_id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Branch code already exists."
                )

        if "email" in update_data:
            existing = (
                db.query(Branch)
                .filter(
                    Branch.email == update_data["email"],
                    Branch.id != branch_id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Branch email already exists."
                )

        for key, value in update_data.items():
            setattr(branch, key, value)

        db.commit()
        db.refresh(branch)

        return branch

    @staticmethod
    def activate_branch(
        db: Session,
        branch_id: int,
    ) -> Branch:
        """
        Activate a branch.
        """

        branch = BranchService.get_branch_by_id(db, branch_id)

        branch.is_active = True

        db.commit()
        db.refresh(branch)

        return branch

    @staticmethod
    def deactivate_branch(
        db: Session,
        branch_id: int,
    ) -> Branch:
        """
        Deactivate a branch.
        """

        branch = BranchService.get_branch_by_id(db, branch_id)

        branch.is_active = False

        db.commit()
        db.refresh(branch)

        return branch

    @staticmethod
    def delete_branch(
        db: Session,
        branch_id: int,
    ):
        """
        Delete a branch.

        Future:
        Prevent deletion if linked with
        Employees,
        Parcels,
        Vehicles,
        Routes.
        """

        branch = BranchService.get_branch_by_id(db, branch_id)

        db.delete(branch)
        db.commit()

        return {
            "message": "Branch deleted successfully."
        }