"""Step 3: Live2D runtime JSON 자동 생성."""
import json
from pathlib import Path


# Live2D 표준 파라미터 매핑
# 파츠 타입 → 생성할 파라미터 목록
PARAM_TEMPLATES = {
    "eye": {
        "left": [
            {"Id": "ParamEyeLOpen", "GroupId": "ParamGroupEye", "Name": "왼쪽 눈 뜨기"},
            {"Id": "ParamEyeLSmile", "GroupId": "ParamGroupEye", "Name": "왼쪽 눈 웃는 얼굴"},
        ],
        "right": [
            {"Id": "ParamEyeROpen", "GroupId": "ParamGroupEye", "Name": "오른쪽 눈 뜨기"},
            {"Id": "ParamEyeRSmile", "GroupId": "ParamGroupEye", "Name": "오른쪽 눈 웃는 얼굴"},
        ],
    },
    "eyebrow": {
        "left": [
            {"Id": "ParamBrowLY", "GroupId": "ParamGroupBrows", "Name": "왼쪽 눈썹 상하"},
        ],
        "right": [
            {"Id": "ParamBrowRY", "GroupId": "ParamGroupBrows", "Name": "오른쪽 눈썹 상하"},
        ],
    },
    "mouth": [
        {"Id": "ParamMouthOpenY", "GroupId": "ParamGroupMouth", "Name": "입 개폐"},
        {"Id": "ParamMouthForm", "GroupId": "ParamGroupMouth", "Name": "입 변형"},
    ],
}

# 항상 포함되는 기본 파라미터
BASE_PARAMS = [
    {"Id": "ParamAngleX", "GroupId": "ParamGroupFace", "Name": "각도 X"},
    {"Id": "ParamAngleY", "GroupId": "ParamGroupFace", "Name": "각도 Y"},
    {"Id": "ParamAngleZ", "GroupId": "ParamGroupFace", "Name": "각도 Z"},
    {"Id": "ParamBodyAngleX", "GroupId": "ParamGroupBody", "Name": "몸의 회전 X"},
    {"Id": "ParamEyeBallX", "GroupId": "ParamGroupEyeballs", "Name": "눈알 X"},
    {"Id": "ParamEyeBallY", "GroupId": "ParamGroupEyeballs", "Name": "눈알 Y"},
    {"Id": "ParamBreath", "GroupId": "ParamGroupBody", "Name": "호흡"},
]

# 파라미터 그룹 정의
PARAM_GROUPS = [
    {"Id": "ParamGroupFace", "GroupId": "", "Name": "얼굴"},
    {"Id": "ParamGroupEye", "GroupId": "", "Name": "눈"},
    {"Id": "ParamGroupEyeballs", "GroupId": "", "Name": "눈알"},
    {"Id": "ParamGroupBrows", "GroupId": "", "Name": "눈썹"},
    {"Id": "ParamGroupMouth", "GroupId": "", "Name": "입"},
    {"Id": "ParamGroupBody", "GroupId": "", "Name": "몸"},
]

# 파츠 이름 → Live2D Part ID 매핑
PART_ID_MAP = {
    "face": "PartFace",
    "left_eye": "PartEyeL",
    "right_eye": "PartEyeR",
    "left_eyebrow": "PartBrowL",
    "right_eyebrow": "PartBrowR",
    "mouth": "PartMouth",
    "nose": "PartNose",
    "hair_front": "PartHairFront",
    "hair_side": "PartHairSide",
    "hair_back": "PartHairBack",
    "left_ear": "PartEarL",
    "right_ear": "PartEarR",
    "neck": "PartNeck",
    "body": "PartBody",
    "left_arm": "PartArmL",
    "right_arm": "PartArmR",
}


def _determine_side(name: str) -> str:
    """파츠 이름에서 좌/우를 판별."""
    if "left" in name:
        return "left"
    elif "right" in name:
        return "right"
    return ""


def generate_cdi3(atlas_info: dict) -> dict:
    """cdi3.json 생성 — 파라미터, 파츠, 그룹 정의."""
    parameters = list(BASE_PARAMS)
    parts_list = []

    # 인식된 파츠에서 파라미터 생성
    seen_param_ids = {p["Id"] for p in parameters}
    for part in atlas_info["parts"]:
        ptype = part["type"]
        side = _determine_side(part["name"])

        # 파라미터 추가
        if ptype in PARAM_TEMPLATES:
            template = PARAM_TEMPLATES[ptype]
            if isinstance(template, dict) and side in template:
                for param in template[side]:
                    if param["Id"] not in seen_param_ids:
                        parameters.append(param)
                        seen_param_ids.add(param["Id"])
            elif isinstance(template, list):
                for param in template:
                    if param["Id"] not in seen_param_ids:
                        parameters.append(param)
                        seen_param_ids.add(param["Id"])

        # 파츠 추가
        part_id = PART_ID_MAP.get(part["name"], f"Part{part['name'].title().replace('_', '')}")
        part_name = part["name"].replace("_", " ").title()
        parts_list.append({"Id": part_id, "Name": part_name})

    return {
        "Version": 3,
        "Parameters": parameters,
        "ParameterGroups": PARAM_GROUPS,
        "Parts": parts_list,
        "CombinedParameters": [
            ["ParamAngleX", "ParamAngleY"],
            ["ParamMouthForm", "ParamMouthOpenY"],
        ],
    }


def generate_model3(atlas_info: dict, model_name: str) -> dict:
    """model3.json 생성 — 모델 구조, 그룹, 파일 참조."""
    return {
        "Version": 3,
        "FileReferences": {
            "Textures": [f"{model_name}.4096/texture_00.png"],
            "DisplayInfo": f"{model_name}.cdi3.json",
        },
        "Groups": [
            {
                "Target": "Parameter",
                "Name": "EyeBlink",
                "Ids": ["ParamEyeLOpen", "ParamEyeROpen"],
            },
            {
                "Target": "Parameter",
                "Name": "LipSync",
                "Ids": ["ParamMouthOpenY"],
            },
        ],
        "HitAreas": [
            {"Id": "HitAreaHead", "Name": "Head"},
            {"Id": "HitAreaBody", "Name": "Body"},
        ],
    }


def generate_runtime(image_path: str | Path, atlas_info: dict, output_dir: str | Path) -> Path:
    """전체 runtime 폴더를 생성한다."""
    output_dir = Path(output_dir)
    model_name = "model"

    # cdi3.json
    cdi3 = generate_cdi3(atlas_info)
    cdi3_path = output_dir / f"{model_name}.cdi3.json"
    with open(cdi3_path, "w", encoding="utf-8") as f:
        json.dump(cdi3, f, indent="\t", ensure_ascii=False)

    # model3.json
    model3 = generate_model3(atlas_info, model_name)
    model3_path = output_dir / f"{model_name}.model3.json"
    with open(model3_path, "w", encoding="utf-8") as f:
        json.dump(model3, f, indent="\t", ensure_ascii=False)

    return output_dir


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m autorig.generator <atlas_info_json> <output_dir>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        atlas_info = json.load(f)

    output_dir = sys.argv[2]
    result_dir = generate_runtime("", atlas_info, output_dir)
    print(f"Runtime 생성 완료: {result_dir}")
