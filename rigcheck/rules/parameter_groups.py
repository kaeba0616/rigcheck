"""파라미터 그룹 일관성 검사: 그룹 미지정 파라미터 감지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_parameter_groups(model: Live2DModel) -> CheckResult:
    """파라미터의 그룹 할당 일관성을 검사한다."""
    result = CheckResult(rule_name="파라미터 그룹 일관성")

    if not model.parameters:
        result.findings.append(Finding(
            rule="parameter_groups",
            severity=Severity.INFO,
            message="파라미터 정보 없음",
            details="cdi3.json에 파라미터 정보가 없습니다.",
        ))
        return result

    # 유효한 그룹 ID 수집
    valid_group_ids = {g["Id"] for g in model.parameter_groups}

    ungrouped = []
    invalid_group = []

    for param in model.parameters:
        group_id = param.get("GroupId", "")
        param_id = param.get("Id", "")

        if not group_id:
            ungrouped.append(param_id)
        elif group_id not in valid_group_ids:
            invalid_group.append((param_id, group_id))

    # 그룹 미지정 파라미터
    if ungrouped:
        result.findings.append(Finding(
            rule="parameter_groups",
            severity=Severity.INFO,
            message=f"그룹 미지정 파라미터 {len(ungrouped)}개",
            details=f"파라미터: {', '.join(ungrouped[:10])}"
                    + (f" 외 {len(ungrouped)-10}개" if len(ungrouped) > 10 else ""),
        ))

    # 존재하지 않는 그룹 참조
    for param_id, group_id in invalid_group:
        result.findings.append(Finding(
            rule="parameter_groups",
            severity=Severity.WARNING,
            message=f"존재하지 않는 그룹 참조: {param_id} → {group_id}",
            details=f"ParameterGroups에 '{group_id}'가 없습니다.",
        ))

    # 빈 그룹 감지
    used_groups = {p.get("GroupId", "") for p in model.parameters if p.get("GroupId")}
    for group in model.parameter_groups:
        group_id = group["Id"]
        if group_id not in used_groups:
            result.findings.append(Finding(
                rule="parameter_groups",
                severity=Severity.INFO,
                message=f"빈 그룹: {group_id} ({group.get('Name', '')})",
                details="이 그룹에 할당된 파라미터가 없습니다.",
            ))

    return result
