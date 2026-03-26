"""RigCheck 규칙 테스트 — 정상 모델과 문제 있는 모델 모두 검증."""
import json
import tempfile
from pathlib import Path

from rigcheck.parser import parse_model
from rigcheck.rules.symmetry import check_symmetry
from rigcheck.rules.required_groups import check_required_groups
from rigcheck.rules.physics import check_physics
from rigcheck.rules.expressions import check_expressions
from rigcheck.rules.parameter_groups import check_parameter_groups
from rigcheck.models import Severity


def _make_model(tmp: Path, model3=None, cdi3=None, physics3=None, expressions=None):
    """테스트용 Live2D 모델 파일 생성."""
    if model3 is None:
        model3 = {
            "Version": 3,
            "FileReferences": {
                "Moc": "test.moc3",
                "Textures": ["test.4096/texture_00.png"],
            },
            "Groups": [
                {"Target": "Parameter", "Name": "EyeBlink", "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]},
                {"Target": "Parameter", "Name": "LipSync", "Ids": ["ParamMouthOpenY"]},
            ],
            "HitAreas": [{"Id": "HitAreaHead", "Name": "Head"}],
        }
    (tmp / "test.model3.json").write_text(json.dumps(model3))

    if cdi3 is None:
        cdi3 = {
            "Version": 3,
            "Parameters": [
                {"Id": "ParamEyeLOpen", "GroupId": "GroupEye", "Name": "왼쪽 눈"},
                {"Id": "ParamEyeROpen", "GroupId": "GroupEye", "Name": "오른쪽 눈"},
                {"Id": "ParamMouthOpenY", "GroupId": "GroupMouth", "Name": "입"},
                {"Id": "ParamAngleX", "GroupId": "GroupFace", "Name": "각도 X"},
            ],
            "ParameterGroups": [
                {"Id": "GroupEye", "GroupId": "", "Name": "눈"},
                {"Id": "GroupMouth", "GroupId": "", "Name": "입"},
                {"Id": "GroupFace", "GroupId": "", "Name": "얼굴"},
            ],
            "Parts": [
                {"Id": "PartEyeL", "Name": "왼쪽 눈"},
                {"Id": "PartEyeR", "Name": "오른쪽 눈"},
                {"Id": "PartBody", "Name": "몸"},
            ],
        }
    (tmp / "test.cdi3.json").write_text(json.dumps(cdi3))

    if physics3:
        (tmp / "test.physics3.json").write_text(json.dumps(physics3))

    if expressions:
        model3.setdefault("FileReferences", {})["Expressions"] = []
        (tmp / "expressions").mkdir(exist_ok=True)
        for i, expr in enumerate(expressions):
            fname = f"expressions/exp_{i:02d}.exp3.json"
            (tmp / fname).write_text(json.dumps(expr))
            model3["FileReferences"]["Expressions"].append({"Name": f"exp_{i:02d}", "File": fname})
        (tmp / "test.model3.json").write_text(json.dumps(model3))

    return parse_model(str(tmp))


# === 대칭성 검사 ===

def test_symmetry_all_paired():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp))
        result = check_symmetry(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert len(warnings) == 0, f"Unexpected warnings: {[w.message for w in warnings]}"


def test_symmetry_unpaired_param():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), cdi3={
            "Version": 3,
            "Parameters": [
                {"Id": "ParamEyeLOpen", "GroupId": "G", "Name": "왼쪽 눈"},
                # ParamEyeROpen 누락!
                {"Id": "ParamAngleX", "GroupId": "G", "Name": "각도"},
            ],
            "ParameterGroups": [{"Id": "G", "GroupId": "", "Name": "G"}],
            "Parts": [],
        })
        result = check_symmetry(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert len(warnings) == 1
        assert "ParamEyeLOpen" in warnings[0].message


def test_symmetry_unpaired_part():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), cdi3={
            "Version": 3,
            "Parameters": [],
            "ParameterGroups": [],
            "Parts": [
                {"Id": "PartArmL", "Name": "왼팔"},
                # PartArmR 누락!
            ],
        })
        result = check_symmetry(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert len(warnings) == 1
        assert "PartArmL" in warnings[0].message


# === 필수 그룹 검사 ===

def test_required_groups_pass():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp))
        result = check_required_groups(model)
        criticals = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert len(criticals) == 0


def test_required_groups_missing_eyeblink():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), model3={
            "Version": 3,
            "FileReferences": {"Moc": "test.moc3", "Textures": ["t.png"]},
            "Groups": [
                {"Target": "Parameter", "Name": "LipSync", "Ids": ["ParamMouthOpenY"]},
                # EyeBlink 누락!
            ],
        })
        result = check_required_groups(model)
        criticals = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert any("EyeBlink" in f.message for f in criticals)


def test_required_groups_missing_lipsync():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), model3={
            "Version": 3,
            "FileReferences": {"Moc": "test.moc3", "Textures": ["t.png"]},
            "Groups": [
                {"Target": "Parameter", "Name": "EyeBlink", "Ids": ["ParamEyeLOpen"]},
                # LipSync 누락!
            ],
        })
        result = check_required_groups(model)
        criticals = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert any("LipSync" in f.message for f in criticals)


# === 물리 설정 검증 ===

def test_physics_normal():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), physics3={
            "Version": 3,
            "Meta": {
                "PhysicsSettingCount": 1,
                "Fps": 60,
                "EffectiveForces": {"Gravity": {"X": 0, "Y": -1}, "Wind": {"X": 0, "Y": 0}},
            },
            "PhysicsSettings": [{
                "Normalization": {
                    "Position": {"Minimum": -10, "Maximum": 10, "Default": 0},
                    "Angle": {"Minimum": -10, "Maximum": 10, "Default": 0},
                },
                "Input": [{"Source": {"Id": "ParamAngleX"}}],
                "Output": [{"Destination": {"Id": "ParamHairFront"}}],
                "Vertices": [],
            }],
        })
        result = check_physics(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert len(warnings) == 0


def test_physics_zero_gravity():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), physics3={
            "Version": 3,
            "Meta": {
                "PhysicsSettingCount": 0,
                "Fps": 60,
                "EffectiveForces": {"Gravity": {"X": 0, "Y": 0}, "Wind": {"X": 0, "Y": 0}},
            },
            "PhysicsSettings": [],
        })
        result = check_physics(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert any("중력" in f.message for f in warnings)


def test_physics_count_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), physics3={
            "Version": 3,
            "Meta": {
                "PhysicsSettingCount": 5,  # 선언은 5개
                "Fps": 60,
                "EffectiveForces": {"Gravity": {"X": 0, "Y": -1}, "Wind": {"X": 0, "Y": 0}},
            },
            "PhysicsSettings": [],  # 실제는 0개
        })
        result = check_physics(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert any("불일치" in f.message for f in warnings)


# === 표정 파라미터 검사 ===

def test_expressions_invalid_param_ref():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), expressions=[{
            "Type": "Live2D Expression",
            "Parameters": [
                {"Id": "ParamNonExistent", "Value": 1, "Blend": "Add"},
            ],
        }])
        result = check_expressions(model)
        warnings = [f for f in result.findings if f.severity == Severity.WARNING]
        assert any("존재하지 않는" in f.message for f in warnings)


# === 파라미터 그룹 일관성 ===

def test_parameter_groups_ungrouped():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), cdi3={
            "Version": 3,
            "Parameters": [
                {"Id": "ParamTest", "GroupId": "", "Name": "테스트"},  # 그룹 없음
            ],
            "ParameterGroups": [{"Id": "GroupA", "GroupId": "", "Name": "A"}],
            "Parts": [],
        })
        result = check_parameter_groups(model)
        infos = [f for f in result.findings if f.severity == Severity.INFO]
        assert any("그룹 미지정" in f.message for f in infos)


def test_parameter_groups_empty_group():
    with tempfile.TemporaryDirectory() as tmp:
        model = _make_model(Path(tmp), cdi3={
            "Version": 3,
            "Parameters": [
                {"Id": "ParamA", "GroupId": "GroupUsed", "Name": "A"},
            ],
            "ParameterGroups": [
                {"Id": "GroupUsed", "GroupId": "", "Name": "사용됨"},
                {"Id": "GroupEmpty", "GroupId": "", "Name": "비어있음"},
            ],
            "Parts": [],
        })
        result = check_parameter_groups(model)
        infos = [f for f in result.findings if f.severity == Severity.INFO]
        assert any("빈 그룹" in f.message for f in infos)


# === 실제 샘플 데이터 테스트 ===

def test_real_sample():
    """실제 Live2D 샘플 모델에서 크래시 없이 동작하는지 확인."""
    import os
    sample_dir = "/home/hidi/dev/gstack/ren_pro_ko/runtime"
    if not os.path.exists(sample_dir):
        return  # 샘플 없으면 스킵

    model = parse_model(sample_dir)
    assert model.name == "ren"
    assert len(model.parameters) > 0
    assert len(model.parts) > 0
    assert len(model.eye_blink_ids) > 0
    assert len(model.lip_sync_ids) > 0

    # 모든 규칙 실행 — 크래시 없어야 함
    for rule_fn in [check_symmetry, check_required_groups, check_physics,
                    check_expressions, check_parameter_groups]:
        result = rule_fn(model)
        assert result.rule_name  # 이름이 있어야 함


if __name__ == "__main__":
    import sys
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
