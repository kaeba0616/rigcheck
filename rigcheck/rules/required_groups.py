"""필수 그룹 검사: EyeBlink, LipSync 등 VTuber 트래킹에 필수적인 그룹 존재 여부."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_required_groups(model: Live2DModel) -> CheckResult:
    """model3.json에 VTuber 트래킹 필수 그룹이 있는지 검사한다."""
    result = CheckResult(rule_name="필수 그룹 검사")

    # EyeBlink — 눈 깜빡임 트래킹에 필수
    if not model.eye_blink_ids:
        result.findings.append(Finding(
            rule="required_groups",
            severity=Severity.CRITICAL,
            message="EyeBlink 그룹 누락",
            details="눈 깜빡임 트래킹이 작동하지 않습니다. "
                    "model3.json의 Groups에 EyeBlink을 추가하세요.",
        ))
    else:
        # Check that referenced parameter IDs actually exist
        param_ids = {p["Id"] for p in model.parameters}
        for blink_id in model.eye_blink_ids:
            if blink_id not in param_ids:
                result.findings.append(Finding(
                    rule="required_groups",
                    severity=Severity.CRITICAL,
                    message=f"EyeBlink 파라미터 참조 오류: {blink_id}",
                    details=f"model3.json에서 참조하는 {blink_id}가 "
                            f"cdi3.json의 파라미터 목록에 없습니다.",
                ))

    # LipSync — 립싱크 트래킹에 필수
    if not model.lip_sync_ids:
        result.findings.append(Finding(
            rule="required_groups",
            severity=Severity.CRITICAL,
            message="LipSync 그룹 누락",
            details="립싱크 트래킹이 작동하지 않습니다. "
                    "model3.json의 Groups에 LipSync을 추가하세요.",
        ))
    else:
        param_ids = {p["Id"] for p in model.parameters}
        for sync_id in model.lip_sync_ids:
            if sync_id not in param_ids:
                result.findings.append(Finding(
                    rule="required_groups",
                    severity=Severity.CRITICAL,
                    message=f"LipSync 파라미터 참조 오류: {sync_id}",
                    details=f"model3.json에서 참조하는 {sync_id}가 "
                            f"cdi3.json의 파라미터 목록에 없습니다.",
                ))

    # HitAreas — 인터랙션에 필요 (필수는 아님)
    if not model.hit_areas:
        result.findings.append(Finding(
            rule="required_groups",
            severity=Severity.INFO,
            message="HitArea 미설정",
            details="터치 반응 영역이 없습니다. 시청자 인터랙션이 필요하면 추가하세요.",
        ))

    # Textures — 최소 1개 필요
    if not model.textures:
        result.findings.append(Finding(
            rule="required_groups",
            severity=Severity.CRITICAL,
            message="텍스처 파일 참조 없음",
            details="model3.json에 텍스처 파일이 지정되지 않았습니다.",
        ))

    return result
