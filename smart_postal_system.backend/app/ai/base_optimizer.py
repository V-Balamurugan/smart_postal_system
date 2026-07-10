from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseOptimizer(ABC):
    """
    Base interface for all optimization algorithms.
    """

    @abstractmethod
    def optimize(
        self,
        *,
        route: Any,
        vehicles: List[Any],
        employees: List[Any],
        parcels: List[Any],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Execute the optimization algorithm and return a standardized result.
        """
        pass