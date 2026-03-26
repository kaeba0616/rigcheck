"""표정 조합 스트레스 테스트: 모든 표정을 동시에 적용했을 때 극단값 감지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel

# 파라미터 값이 이 범위를 넘으면 경고
EXTREME_THRESHOLD = 2.0


def check_expression_stress(model: Live2DModel) -> CheckResult:
    """모든 표정을 동시에 적용했을 때 파라미터가 극단으로 가는지 시뮬레이션."""
    result = CheckResult(rule_name="표정 조합 스트레스 테스트")

    if len(model.expressions) < 2:
        result.findings.append(Finding(
            rule="expression_stress",
            severity=Severity.INFO,
            message=f"표정 파일 {len(model.expressions)}개 — 조합 테스트 불필요",
            details="표정이 2개 미만이면 조합 충돌이 발생하지 않습니다.",
        ))
        return result

    # 각 표정의 파라미터 값과 Blend 모드 수집
    # Blend 모드별 시뮬레이션:
    #   Add: base + value
    #   Multiply: base * value
    #   Overwrite: value (마지막 적용이 이김)

    # 모든 표정을 Add로 합산했을 때의 극단값 검사
    param_totals: dict[str, float] = {}  # param_id -> 합산값
    param_sources: dict[str, list[str]] = {}  # param_id -> [file_names]

    for expr in model.expressions:
        file_name = expr.get("file", "unknown")
        for param in expr.get("Parameters", []):
            param_id = param.get("Id", "")
            value = param.get("Value", 0)
            blend = param.get("Blend", "Add")

            if not param_id or not isinstance(value, (int, float)):
                continue

            if param_id not in param_totals:
                param_totals[param_id] = 0
                param_sources[param_id] = []

            if blend == "Add":
                param_totals[param_id] += value
            elif blend == "Multiply":
                # Multiply는 기본값(보통 1)에 곱하는 것이므로 누적 곱
                if param_totals[param_id] == 0:
                    param_totals[param_id] = value
                else:
                    param_totals[param_id] *= value
            # Overwrite는 마지막 값만 유효하므로 극단값 문제 없음

            param_sources[param_id].append(file_name)

    # 극단값 감지
    extreme_params = []
    for param_id, total in param_totals.items():
        if abs(total) > EXTREME_THRESHOLD:
            extreme_params.append((param_id, total, param_sources[param_id]))

    if extreme_params:
        for param_id, total, sources in extreme_params:
            result.findings.append(Finding(
                rule="expression_stress",
                severity=Severity.WARNING,
                message=f"표정 합산 시 극단값: {param_id} = {total:.2f}",
                details=f"관련 표정: {', '.join(set(sources))}. "
                        f"모든 표정이 동시에 적용되면 값이 {total:.2f}까지 갈 수 있습니다. "
                        f"얼굴이 일그러질 수 있으니 Blend 모드를 확인하세요.",
            ))
    else:
        result.findings.append(Finding(
            rule="expression_stress",
            severity=Severity.INFO,
            message=f"표정 조합 안전 — {len(model.expressions)}개 표정 합산 테스트 통과",
        ))

    return result
