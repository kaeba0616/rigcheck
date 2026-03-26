"""물리 설정 검증: physics3.json의 파라미터 값 범위 이상치 감지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_physics(model: Live2DModel) -> CheckResult:
    """물리 시뮬레이션 설정의 이상치를 검사한다."""
    result = CheckResult(rule_name="물리 설정 검증")

    if not model.physics_settings and not model.physics_meta:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.INFO,
            message="물리 설정 파일 없음",
            details="physics3.json이 없습니다. 머리카락/옷 등의 흔들림이 작동하지 않습니다.",
        ))
        return result

    meta = model.physics_meta
    fps = meta.get("Fps", 0)

    # FPS 검사
    if fps <= 0:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.WARNING,
            message=f"물리 FPS가 비정상: {fps}",
            details="FPS가 0 이하입니다. 물리 시뮬레이션이 작동하지 않을 수 있습니다.",
        ))
    elif fps < 30:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.WARNING,
            message=f"물리 FPS가 낮음: {fps}",
            details="30 미만의 FPS는 물리 시뮬레이션이 부자연스러울 수 있습니다.",
        ))

    # Gravity 검사
    gravity = meta.get("EffectiveForces", {}).get("Gravity", {})
    grav_x = gravity.get("X", 0)
    grav_y = gravity.get("Y", 0)

    if grav_y == 0 and grav_x == 0:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.WARNING,
            message="중력이 0으로 설정됨",
            details="중력이 없으면 머리카락/옷이 떠다닙니다. 의도적이 아니라면 Y=-1을 권장합니다.",
        ))
    elif grav_y > 0:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.WARNING,
            message=f"중력 방향이 위쪽: Y={grav_y}",
            details="중력이 위를 향합니다. 의도적인 무중력 표현이 아니라면 확인하세요.",
        ))

    # 물리 설정 개수 정합성
    declared_count = meta.get("PhysicsSettingCount", 0)
    actual_count = len(model.physics_settings)
    if declared_count != actual_count:
        result.findings.append(Finding(
            rule="physics",
            severity=Severity.WARNING,
            message=f"물리 설정 개수 불일치: 선언={declared_count}, 실제={actual_count}",
            details="Meta.PhysicsSettingCount와 실제 PhysicsSettings 배열 길이가 다릅니다.",
        ))

    # 각 물리 설정 검사
    for i, setting in enumerate(model.physics_settings):
        normalization = setting.get("Normalization", {})

        # Position normalization
        pos_norm = normalization.get("Position", {})
        pos_min = pos_norm.get("Minimum", 0)
        pos_max = pos_norm.get("Maximum", 0)
        if pos_max <= pos_min and pos_norm:
            result.findings.append(Finding(
                rule="physics",
                severity=Severity.WARNING,
                message=f"물리 설정 #{i+1}: Position 정규화 범위 오류",
                details=f"Minimum({pos_min}) >= Maximum({pos_max}). 물리가 제대로 작동하지 않습니다.",
            ))

        # Angle normalization
        angle_norm = normalization.get("Angle", {})
        angle_min = angle_norm.get("Minimum", 0)
        angle_max = angle_norm.get("Maximum", 0)
        if angle_max <= angle_min and angle_norm:
            result.findings.append(Finding(
                rule="physics",
                severity=Severity.WARNING,
                message=f"물리 설정 #{i+1}: Angle 정규화 범위 오류",
                details=f"Minimum({angle_min}) >= Maximum({angle_max}). 물리가 제대로 작동하지 않습니다.",
            ))

        # Input/Output 존재 여부
        inputs = setting.get("Input", [])
        outputs = setting.get("Output", [])
        if not inputs:
            result.findings.append(Finding(
                rule="physics",
                severity=Severity.WARNING,
                message=f"물리 설정 #{i+1}: 입력 파라미터 없음",
                details="Input이 비어있어 물리가 반응하지 않습니다.",
            ))
        if not outputs:
            result.findings.append(Finding(
                rule="physics",
                severity=Severity.WARNING,
                message=f"물리 설정 #{i+1}: 출력 파라미터 없음",
                details="Output이 비어있어 물리 결과가 표시되지 않습니다.",
            ))

    return result
