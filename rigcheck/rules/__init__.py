"""검사 규칙 모듈."""
from .symmetry import check_symmetry
from .required_groups import check_required_groups
from .physics import check_physics
from .expressions import check_expressions
from .parameter_groups import check_parameter_groups
from .naming import check_naming
from .unused import check_unused
from .combinations import check_combinations

ALL_RULES = [
    check_symmetry,
    check_required_groups,
    check_physics,
    check_expressions,
    check_parameter_groups,
    check_naming,
    check_unused,
    check_combinations,
]
