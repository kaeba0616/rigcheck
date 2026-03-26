"""파라미터 조합 검사: CombinedParameters 유효성 + 표정 간 Blend 모드 충돌."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_combinations(model: Live2DModel) -> CheckResult:
    """파라미터 조합의 유효성과 표정 간 충돌을 검사한다."""
    result = CheckResult(rule_name="파라미터 조합 검사")

    defined_params = {p["Id"] for p in model.parameters}

    # CombinedParameters 유효성
    for i, combo in enumerate(model.combined_parameters):
        if len(combo) < 2:
            result.findings.append(Finding(
                rule="combinations",
                severity=Severity.WARNING,
                message=f"조합 #{i+1}: 파라미터가 2개 미만 ({len(combo)}개)",
                details="CombinedParameters는 최소 2개의 파라미터가 필요합니다.",
            ))

        for param_id in combo:
            if param_id not in defined_params:
                result.findings.append(Finding(
                    rule="combinations",
                    severity=Severity.WARNING,
                    message=f"조합 #{i+1}: 존재하지 않는 파라미터 '{param_id}'",
                    details="CombinedParameters에서 참조하는 파라미터가 cdi3.json에 없습니다.",
                ))

    # 표정 간 Blend 모드 충돌 감지
    # 같은 파라미터를 다른 표정에서 다른 Blend 모드로 사용하면 예측 불가능
    param_blends: dict[str, dict[str, str]] = {}  # param_id -> {file: blend_mode}

    for expr in model.expressions:
        file_name = expr.get("file", "unknown")
        for param in expr.get("Parameters", []):
            param_id = param.get("Id", "")
            blend = param.get("Blend", "")
            if not param_id or not blend:
                continue

            if param_id not in param_blends:
                param_blends[param_id] = {}
            param_blends[param_id][file_name] = blend

    # 같은 파라미터에 대해 서로 다른 Blend 모드가 사용되는지 확인
    for param_id, blends_by_file in param_blends.items():
        unique_blends = set(blends_by_file.values())
        if len(unique_blends) > 1:
            files_detail = ", ".join(
                f"{f}({b})" for f, b in blends_by_file.items()
            )
            result.findings.append(Finding(
                rule="combinations",
                severity=Severity.INFO,
                message=f"Blend 모드 불일치: {param_id}",
                details=f"표정 파일마다 다른 Blend 모드 사용: {files_detail}. "
                        f"표정 전환 시 예측과 다른 결과가 나올 수 있습니다.",
            ))

    return result
