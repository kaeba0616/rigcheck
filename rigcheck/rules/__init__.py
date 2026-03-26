"""검사 규칙 모듈."""
from .symmetry import check_symmetry
from .required_groups import check_required_groups
from .physics import check_physics
from .expressions import check_expressions
from .parameter_groups import check_parameter_groups

ALL_RULES = [
    check_symmetry,
    check_required_groups,
    check_physics,
    check_expressions,
    check_parameter_groups,
]
