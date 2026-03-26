"""Unused Nodes 감지: 어디에서도 참조되지 않는 파라미터/파츠 탐지."""
import re
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def _collect_referenced_param_ids(model: Live2DModel) -> set[str]:
    """물리, 표정, 모션, 모델 그룹에서 참조되는 파라미터 ID를 수집."""
    referenced = set()

    # EyeBlink / LipSync 그룹
    referenced.update(model.eye_blink_ids)
    referenced.update(model.lip_sync_ids)

    # 물리 설정 — Input/Output의 Source/Destination Id
    for setting in model.physics_settings:
        for inp in setting.get("Input", []):
            src = inp.get("Source", {})
            if "Id" in src:
                referenced.add(src["Id"])
        for out in setting.get("Output", []):
            dst = out.get("Destination", {})
            if "Id" in dst:
                referenced.add(dst["Id"])

    # 표정 파일
    for expr in model.expressions:
        for param in expr.get("Parameters", []):
            if "Id" in param:
                referenced.add(param["Id"])

    # 모션 파일 — Curves의 Id
    for motion in model.motions:
        for curve in motion.get("Curves", []):
            if "Id" in curve:
                referenced.add(curve["Id"])

    # CombinedParameters
    for combo in model.combined_parameters:
        referenced.update(combo)

    return referenced


def check_unused(model: Live2DModel) -> CheckResult:
    """어디에서도 참조되지 않는 파라미터와 파츠를 감지한다."""
    result = CheckResult(rule_name="미사용 노드 감지")

    if not model.parameters:
        return result

    referenced_params = _collect_referenced_param_ids(model)
    defined_params = {p["Id"] for p in model.parameters}

    # 정의됐지만 어디서도 참조 안 되는 파라미터
    unused_params = defined_params - referenced_params
    if unused_params:
        # 일부 파라미터는 트래킹 소프트웨어가 직접 사용하므로 제외
        tracking_params = {
            "ParamAngleX", "ParamAngleY", "ParamAngleZ",
            "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ",
            "ParamEyeBallX", "ParamEyeBallY",
        }
        truly_unused = unused_params - tracking_params
        if truly_unused:
            result.findings.append(Finding(
                rule="unused",
                severity=Severity.INFO,
                message=f"미사용 파라미터 {len(truly_unused)}개",
                details=f"물리/표정/모션/그룹 어디에서도 참조되지 않음: "
                        f"{', '.join(sorted(truly_unused)[:10])}"
                        + (f" 외 {len(truly_unused)-10}개" if len(truly_unused) > 10 else ""),
            ))

    # 물리/표정/모션에서 참조하지만 cdi3에 정의 안 된 파라미터 (역방향)
    phantom_params = referenced_params - defined_params
    if phantom_params:
        result.findings.append(Finding(
            rule="unused",
            severity=Severity.WARNING,
            message=f"정의되지 않은 파라미터 참조 {len(phantom_params)}개",
            details=f"물리/표정/모션에서 사용하지만 cdi3.json에 없음: "
                    f"{', '.join(sorted(phantom_params)[:10])}"
                    + (f" 외 {len(phantom_params)-10}개" if len(phantom_params) > 10 else ""),
        ))

    return result
