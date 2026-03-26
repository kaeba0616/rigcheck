"""검사 규칙 모듈."""
from .symmetry import check_symmetry
from .required_groups import check_required_groups
from .physics import check_physics
from .expressions import check_expressions
from .parameter_groups import check_parameter_groups
from .naming import check_naming
from .unused import check_unused
from .combinations import check_combinations
from .motion_analysis import check_motion_analysis
from .expression_stress import check_expression_stress
from .physics_chain import check_physics_chain
from .file_integrity import check_file_integrity

ALL_RULES = [
    check_symmetry,
    check_required_groups,
    check_physics,
    check_expressions,
    check_parameter_groups,
    check_naming,
    check_unused,
    check_combinations,
    check_motion_analysis,
    check_expression_stress,
    check_physics_chain,
    check_file_integrity,
]
