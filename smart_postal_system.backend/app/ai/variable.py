"""
OR-Tools CP-SAT Variable Builder
=================================

Encapsulates all CP-SAT decision variable creation for the postal
route optimization model.

Decision Variables
------------------
- ``vehicle_selected[v]`` : BoolVar — is vehicle *v* selected?
- ``employee_selected[e]`` : BoolVar — is employee *e* selected?
- ``parcel_pos[p]``        : IntVar  — delivery-sequence position of parcel *p* (0..N-1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ortools.sat.python.cp_model import CpModel, IntVar


@dataclass(frozen=True)
class VariableSet:
    """Typed container for all CP-SAT decision variables."""

    vehicle_selected: List[IntVar]
    """BoolVar per vehicle — exactly one must be True."""

    employee_selected: List[IntVar]
    """BoolVar per employee — exactly one must be True."""

    parcel_positions: List[IntVar]
    """IntVar per parcel — position in delivery sequence (0..n_parcels-1)."""

    n_vehicles: int
    n_employees: int
    n_parcels: int


class ORToolsVariableBuilder:
    """
    Factory that creates the CP-SAT decision variables on a given model.
    """

    @staticmethod
    def build(
        model: CpModel,
        *,
        n_vehicles: int,
        n_employees: int,
        n_parcels: int,
    ) -> VariableSet:
        """
        Create and return all decision variables.

        Parameters
        ----------
        model : CpModel
            The CP-SAT model to add variables to.
        n_vehicles : int
            Number of candidate vehicles.
        n_employees : int
            Number of candidate employees.
        n_parcels : int
            Number of parcels to sequence.

        Returns
        -------
        VariableSet
            Frozen dataclass holding all variable lists.
        """
        vehicle_selected = [
            model.new_bool_var(f"veh_{i}")
            for i in range(n_vehicles)
        ]

        employee_selected = [
            model.new_bool_var(f"emp_{i}")
            for i in range(n_employees)
        ]

        parcel_positions = [
            model.new_int_var(0, n_parcels - 1, f"parcel_{p}")
            for p in range(n_parcels)
        ]

        return VariableSet(
            vehicle_selected=vehicle_selected,
            employee_selected=employee_selected,
            parcel_positions=parcel_positions,
            n_vehicles=n_vehicles,
            n_employees=n_employees,
            n_parcels=n_parcels,
        )
