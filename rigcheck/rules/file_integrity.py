"""텍스처/파일 참조 무결성: model3.json에서 참조하는 파일이 실제로 존재하는지."""
from pathlib import Path
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_file_integrity(model: Live2DModel) -> CheckResult:
    """model3.json에서 참조하는 모든 파일이 실제로 존재하는지 검사한다."""
    result = CheckResult(rule_name="파일 참조 무결성")

    base = model.base_path
    missing_files = []
    checked_files = []

    # 텍스처 파일
    for tex in model.textures:
        tex_path = base / tex
        checked_files.append(tex)
        if not tex_path.exists():
            missing_files.append(("텍스처", tex))

    # Moc 파일
    if model.moc_file:
        moc_path = base / model.moc_file
        checked_files.append(model.moc_file)
        if not moc_path.exists():
            missing_files.append(("모델(moc3)", model.moc_file))

    # 표정 파일
    for expr_file in model.expression_files:
        expr_path = base / expr_file
        checked_files.append(expr_file)
        if not expr_path.exists():
            missing_files.append(("표정", expr_file))

    # 모션 파일
    for motion_file in model.motion_files:
        motion_path = base / motion_file
        checked_files.append(motion_file)
        if not motion_path.exists():
            missing_files.append(("모션", motion_file))

    # 결과 보고
    if missing_files:
        for file_type, file_name in missing_files:
            result.findings.append(Finding(
                rule="file_integrity",
                severity=Severity.CRITICAL,
                message=f"누락된 {file_type} 파일: {file_name}",
                details=f"model3.json에서 참조하지만 실제 파일이 없습니다. "
                        f"런타임에서 로드 실패가 발생합니다.",
            ))
    else:
        result.findings.append(Finding(
            rule="file_integrity",
            severity=Severity.INFO,
            message=f"파일 참조 무결성 확인 — {len(checked_files)}개 파일 모두 존재",
        ))

    return result
