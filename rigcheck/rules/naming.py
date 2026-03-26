"""Naming Convention 체크: 파라미터/파츠 ID가 Live2D 표준 규칙을 따르는지."""
import re
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel

# Live2D 표준 접두사
PARAM_PREFIX = "Param"
PART_PREFIX = "Part"

# ID에 허용되는 문자: 영문, 숫자, 밑줄
VALID_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def check_naming(model: Live2DModel) -> CheckResult:
    """파라미터와 파츠의 네이밍 규칙을 검사한다."""
    result = CheckResult(rule_name="네이밍 규칙 검사")

    # 중복 ID 감지
    all_param_ids = [p["Id"] for p in model.parameters]
    all_part_ids = [p["Id"] for p in model.parts]

    seen_param = {}
    for pid in all_param_ids:
        if pid in seen_param:
            seen_param[pid] += 1
        else:
            seen_param[pid] = 1
    for pid, count in seen_param.items():
        if count > 1:
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.WARNING,
                message=f"중복 파라미터 ID: {pid} ({count}회)",
                details="같은 ID가 여러 번 정의되었습니다. 예측 불가능한 동작을 유발할 수 있습니다.",
            ))

    seen_part = {}
    for pid in all_part_ids:
        if pid in seen_part:
            seen_part[pid] += 1
        else:
            seen_part[pid] = 1
    for pid, count in seen_part.items():
        if count > 1:
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.WARNING,
                message=f"중복 파츠 ID: {pid} ({count}회)",
                details="같은 ID가 여러 번 정의되었습니다.",
            ))

    # 파라미터 접두사 검사
    for param in model.parameters:
        pid = param.get("Id", "")
        if not pid:
            continue

        if not VALID_ID_PATTERN.match(pid):
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.WARNING,
                message=f"비표준 파라미터 ID 문자: {pid}",
                details="ID는 영문으로 시작하고, 영문/숫자/밑줄만 포함해야 합니다.",
            ))
        elif not pid.startswith(PARAM_PREFIX):
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.INFO,
                message=f"비표준 파라미터 접두사: {pid}",
                details=f"Live2D 표준은 '{PARAM_PREFIX}' 접두사입니다. 동작에는 문제 없습니다.",
            ))

    # 파츠 접두사 검사
    for part in model.parts:
        pid = part.get("Id", "")
        if not pid:
            continue

        if not VALID_ID_PATTERN.match(pid):
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.WARNING,
                message=f"비표준 파츠 ID 문자: {pid}",
                details="ID는 영문으로 시작하고, 영문/숫자/밑줄만 포함해야 합니다.",
            ))
        elif not pid.startswith(PART_PREFIX):
            result.findings.append(Finding(
                rule="naming",
                severity=Severity.INFO,
                message=f"비표준 파츠 접두사: {pid}",
                details=f"Live2D 표준은 '{PART_PREFIX}' 접두사입니다. 동작에는 문제 없습니다.",
            ))

    return result
