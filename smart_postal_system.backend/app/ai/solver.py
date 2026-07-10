"""
OR-Tools CP-SAT Solver Wrapper
===============================

Thin wrapper around ``cp_model.CpSolver`` that provides:

- Configurable time limit and worker count.
- A typed ``SolverResult`` return value.
- Automatic status checking with descriptive error messages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ortools.sat.python.cp_model import CpModel, CpSolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SolverResult:
    """Immutable container for the solver outcome."""

    solver: "CpSolver"
    """The underlying CpSolver, used to extract variable values."""

    status: int
    """Raw OR-Tools status constant (OPTIMAL, FEASIBLE, INFEASIBLE, …)."""

    status_name: str
    """Human-readable status string (e.g. ``'OPTIMAL'``)."""

    objective_value: float
    """Objective value of the best solution found."""

    is_feasible: bool
    """True when the solver found at least one feasible solution."""


class ORToolsSolver:
    """
    Configurable wrapper around the CP-SAT solver.

    Parameters
    ----------
    max_time_seconds : float
        Hard wall-clock time limit.
    num_workers : int
        Number of search workers (1 = deterministic).
    log_search : bool
        Whether to log OR-Tools internal search progress.
    """

    def __init__(
        self,
        *,
        max_time_seconds: float = 5.0,
        num_workers: int = 1,
        log_search: bool = False,
    ):
        self.max_time_seconds = max_time_seconds
        self.num_workers = num_workers
        self.log_search = log_search

    def solve(self, model: "CpModel") -> SolverResult:
        """
        Run the solver on *model* and return a ``SolverResult``.

        Raises
        ------
        ValueError
            If the solver finds no feasible solution (INFEASIBLE / UNKNOWN).
        """
        from ortools.sat.python import cp_model

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_time_seconds
        solver.parameters.log_search_progress = self.log_search
        solver.parameters.num_workers = self.num_workers

        status = solver.solve(model)
        status_name = solver.status_name(status)
        is_feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        logger.info("OR-Tools CP-SAT solver status: %s", status_name)

        if not is_feasible:
            raise ValueError(
                f"OR-Tools CP-SAT found no feasible solution "
                f"(status={status_name}). Falling back to Rule-Based engine."
            )

        return SolverResult(
            solver=solver,
            status=status,
            status_name=status_name,
            objective_value=solver.objective_value,
            is_feasible=True,
        )
