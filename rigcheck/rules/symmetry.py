"""좌우 대칭성 검사: L/R 파라미터 및 파츠 쌍 매칭."""
import re
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel

# L/R 쌍을 식별하기 위한 패턴들
# ParamEyeLOpen -> ("ParamEye", "L", "Open")
# PartArmR -> ("PartArm", "R", "")
LR_PATTERNS = [
    # 중간에 L/R: ParamEyeLOpen, ParamBrowLY
    re.compile(r"^(.+?)(L|R)(\d*(?:[A-Z].*)?)?$"),
]


def _find_lr_pairs(ids: list[str]) -> tuple[dict[str, str], list[str]]:
    """
    ID 목록에서 L/R 쌍을 찾는다.
    Returns: (paired: {left_id: right_id}, unpaired: [ids])
    """
    left_ids: dict[str, str] = {}   # canonical -> original_id
    right_ids: dict[str, str] = {}  # canonical -> original_id
    non_lr: list[str] = []

    for id_ in ids:
        matched = False
        for pattern in LR_PATTERNS:
            m = pattern.match(id_)
            if m:
                prefix, side, suffix = m.group(1), m.group(2), m.group(3) or ""
                canonical = f"{prefix}__{suffix}"
                if side == "L":
                    left_ids[canonical] = id_
                else:
                    right_ids[canonical] = id_
                matched = True
                break
        if not matched:
            non_lr.append(id_)

    # Find paired and unpaired
    paired = {}
    unpaired = []

    all_canonicals = set(left_ids.keys()) | set(right_ids.keys())
    for canonical in all_canonicals:
        l_id = left_ids.get(canonical)
        r_id = right_ids.get(canonical)
        if l_id and r_id:
            paired[l_id] = r_id
        elif l_id:
            unpaired.append(l_id)
        elif r_id:
            unpaired.append(r_id)

    return paired, unpaired


def check_symmetry(model: Live2DModel) -> CheckResult:
    """파라미터와 파츠의 L/R 대칭성을 검사한다."""
    result = CheckResult(rule_name="좌우 대칭성 검사")

    # Check parameters
    param_ids = [p["Id"] for p in model.parameters]
    param_paired, param_unpaired = _find_lr_pairs(param_ids)

    for unpaired_id in param_unpaired:
        # Find the parameter name for better reporting
        param_name = next(
            (p.get("Name", "") for p in model.parameters if p["Id"] == unpaired_id),
            ""
        )
        result.findings.append(Finding(
            rule="symmetry",
            severity=Severity.WARNING,
            message=f"짝 없는 파라미터: {unpaired_id}",
            details=f"이름: {param_name}. L/R 쌍이 존재하지 않습니다.",
        ))

    # Check parts
    part_ids = [p["Id"] for p in model.parts]
    part_paired, part_unpaired = _find_lr_pairs(part_ids)

    for unpaired_id in part_unpaired:
        part_name = next(
            (p.get("Name", "") for p in model.parts if p["Id"] == unpaired_id),
            ""
        )
        result.findings.append(Finding(
            rule="symmetry",
            severity=Severity.WARNING,
            message=f"짝 없는 파츠: {unpaired_id}",
            details=f"이름: {part_name}. L/R 쌍이 존재하지 않습니다.",
        ))

    # Info: report paired counts
    if param_paired or part_paired:
        result.findings.append(Finding(
            rule="symmetry",
            severity=Severity.INFO,
            message=f"대칭 쌍 발견: 파라미터 {len(param_paired)}쌍, 파츠 {len(part_paired)}쌍",
        ))

    return result
