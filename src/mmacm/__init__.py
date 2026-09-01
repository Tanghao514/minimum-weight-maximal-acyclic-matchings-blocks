from .core import SolveResult, UnsupportedBlockError
from .solver import solve_min_weight_maximal_acyclic_matching
from .checker import (
    check_matching,
    check_acyclic_matching,
    check_maximal_acyclic_matching,
    check_maximal_acyclic_matching_fast,
    verify_solution,
)

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "SolveResult",
    "UnsupportedBlockError",
    "solve_min_weight_maximal_acyclic_matching",
    "check_matching",
    "check_acyclic_matching",
    "check_maximal_acyclic_matching",
    "check_maximal_acyclic_matching_fast",
    "verify_solution",
]
