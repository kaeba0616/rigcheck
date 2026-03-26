"""표정 파라미터 범위 검사: exp3.json의 값이 유효 범위 내인지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_expressions(model: Live2DModel) -> CheckResult:
    """표정 데이터의 파라미터 값이 유효한지 검사한다."""
    result = CheckResult(rule_name="표정 파라미터 검사")

    if not model.expressions:
        result.findings.append(Finding(
            rule="expressions",
            severity=Severity.INFO,
            message="표정 파일 없음",
            details="exp3.json 파일이 없습니다. 표정 전환 기능이 작동하지 않습니다.",
        ))
        return result

    param_ids = {p["Id"] for p in model.parameters}

    for expr in model.expressions:
        file_name = expr.get("file", "unknown")
        parameters = expr.get("Parameters", [])

        if not parameters:
            result.findings.append(Finding(
                rule="expressions",
                severity=Severity.WARNING,
                message=f"{file_name}: 파라미터 없음",
                details="표정 파일에 변경할 파라미터가 없습니다.",
            ))
            continue

        for param in parameters:
            param_id = param.get("Id", "")
            value = param.get("Value", 0)
            blend = param.get("Blend", "")

            # 존재하지 않는 파라미터 참조
            if param_id and param_id not in param_ids:
                result.findings.append(Finding(
                    rule="expressions",
                    severity=Severity.WARNING,
                    message=f"{file_name}: 존재하지 않는 파라미터 참조 '{param_id}'",
                    details="cdi3.json에 이 파라미터가 없습니다. 표정 전환 시 무시됩니다.",
                ))

            # 극단적 값 경고 (일반적으로 0~1 범위)
            if isinstance(value, (int, float)) and (value < -10 or value > 10):
                result.findings.append(Finding(
                    rule="expressions",
                    severity=Severity.WARNING,
                    message=f"{file_name}: 극단적 파라미터 값 {param_id}={value}",
                    details="일반적인 파라미터 범위(-10~10)를 벗어났습니다. 의도적인지 확인하세요.",
                ))

            # Blend 모드 검사
            valid_blends = {"Add", "Multiply", "Overwrite"}
            if blend and blend not in valid_blends:
                result.findings.append(Finding(
                    rule="expressions",
                    severity=Severity.WARNING,
                    message=f"{file_name}: 알 수 없는 Blend 모드 '{blend}'",
                    details=f"유효한 Blend 모드: {', '.join(valid_blends)}",
                ))

    return result
