"""모션 키프레임 분석: 급격한 값 변화(프레임 간 점프) 감지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel

# 프레임 간 값 변화가 이 임계값을 넘으면 경고
# Live2D 파라미터는 -30~30 범위도 흔함. 전체 범위의 30% 이상 변화를 감지.
JUMP_THRESHOLD = 10.0


def check_motion_analysis(model: Live2DModel) -> CheckResult:
    """모션 데이터에서 부자연스러운 키프레임 점프를 감지한다."""
    result = CheckResult(rule_name="모션 키프레임 분석")

    if not model.motions:
        result.findings.append(Finding(
            rule="motion_analysis",
            severity=Severity.INFO,
            message="모션 파일 없음",
            details="motion3.json 파일이 없습니다. 아이들 모션 등을 추가하면 캐릭터가 더 자연스럽습니다.",
        ))
        return result

    for motion in model.motions:
        file_name = motion.get("file", "unknown")
        curves = motion.get("Curves", [])
        meta = motion.get("Meta", {})
        duration = meta.get("Duration", 0)
        fps = meta.get("Fps", 30)

        if not curves:
            result.findings.append(Finding(
                rule="motion_analysis",
                severity=Severity.WARNING,
                message=f"{file_name}: 커브 데이터 없음",
                details="모션 파일에 애니메이션 커브가 없습니다.",
            ))
            continue

        for curve in curves:
            target = curve.get("Target", "")
            curve_id = curve.get("Id", "")
            segments = curve.get("Segments", [])

            if not segments or len(segments) < 4:
                continue

            # Live2D 모션 세그먼트 형식:
            # [value, type, time, value, type, time, value, ...]
            # type 0 = linear, type 1 = bezier, type 2 = stepped, type 3 = inverse stepped
            # 값을 추출해서 연속 프레임 간 점프 감지
            values = []
            i = 0
            if len(segments) > 0:
                values.append(segments[0])  # 첫 번째 값
                i = 1

            while i < len(segments):
                seg_type = segments[i] if i < len(segments) else 0

                if seg_type == 0:  # linear: time, value
                    if i + 2 < len(segments):
                        values.append(segments[i + 2])
                    i += 3
                elif seg_type == 1:  # bezier: time, value, time, value, time, value
                    if i + 6 < len(segments):
                        values.append(segments[i + 6])
                    i += 7
                elif seg_type == 2 or seg_type == 3:  # stepped: time, value
                    if i + 2 < len(segments):
                        values.append(segments[i + 2])
                    i += 3
                else:
                    i += 1

            # 연속 값 간 점프 감지
            jumps = []
            for j in range(1, len(values)):
                if not isinstance(values[j], (int, float)) or not isinstance(values[j-1], (int, float)):
                    continue
                diff = abs(values[j] - values[j-1])
                if diff > JUMP_THRESHOLD:
                    jumps.append((j, diff))

            if jumps:
                worst = max(jumps, key=lambda x: x[1])
                result.findings.append(Finding(
                    rule="motion_analysis",
                    severity=Severity.WARNING,
                    message=f"{file_name}: {curve_id} 급격한 값 변화 ({len(jumps)}회)",
                    details=f"최대 변화량: {worst[1]:.2f} (키프레임 #{worst[0]}). "
                            f"부자연스러운 움직임의 원인일 수 있습니다. "
                            f"stepped 타입이 의도적이라면 무시해도 됩니다.",
                ))

    return result
