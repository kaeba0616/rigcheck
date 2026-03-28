"""Step 1: Grok Vision으로 캐릭터 파츠 인식."""
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PARTS_PROMPT = """이 캐릭터 일러스트를 분석해서 각 파츠의 위치를 JSON으로 출력해주세요.

다음 파츠들을 찾아주세요 (존재하는 것만):
- left_eye (왼쪽 눈)
- right_eye (오른쪽 눈)
- left_eyebrow (왼쪽 눈썹)
- right_eyebrow (오른쪽 눈썹)
- mouth (입)
- nose (코)
- face (얼굴 전체)
- hair_front (앞머리)
- hair_side (옆머리)
- hair_back (뒷머리)
- left_ear (왼쪽 귀)
- right_ear (오른쪽 귀)
- neck (목)
- body (몸통)
- left_arm (왼팔)
- right_arm (오른팔)

출력 형식 (JSON만, 설명 없이):
{
  "image_width": 이미지 가로 픽셀,
  "image_height": 이미지 세로 픽셀,
  "parts": [
    {
      "name": "파츠 이름",
      "type": "eye|eyebrow|mouth|nose|face|hair|ear|neck|body|arm",
      "bbox": [x1, y1, x2, y2],
      "z_order": 숫자 (높을수록 앞에 그려짐, 0-10 범위)
    }
  ]
}

좌표는 이미지 왼쪽 위가 (0,0), 오른쪽 아래가 (width, height)입니다.
bbox는 [왼쪽, 위, 오른쪽, 아래] 순서입니다.
JSON만 출력하세요. 마크다운 코드블록이나 설명은 넣지 마세요."""


def analyze_image(image_path: str | Path) -> dict:
    """이미지를 Grok Vision API로 분석하여 파츠 정보를 반환한다."""
    image_path = Path(image_path)

    # 이미지를 base64로 인코딩
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # 확장자로 MIME 타입 결정
    suffix = image_path.suffix.lower()
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    mime_type = mime_types.get(suffix, "image/png")

    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )

    response = client.chat.completions.create(
        model="grok-4-1-fast-non-reasoning",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                        },
                    },
                    {
                        "type": "text",
                        "text": PARTS_PROMPT,
                    },
                ],
            }
        ],
        temperature=0,
    )

    raw_text = response.choices[0].message.content.strip()

    # JSON 파싱 (마크다운 코드블록 제거)
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        # 첫 줄(```json)과 마지막 줄(```) 제거
        json_lines = []
        inside = False
        for line in lines:
            if line.startswith("```") and not inside:
                inside = True
                continue
            elif line.startswith("```") and inside:
                break
            elif inside:
                json_lines.append(line)
        raw_text = "\n".join(json_lines)

    result = json.loads(raw_text)

    # 실제 이미지 크기로 좌표 보정
    from PIL import Image
    img = Image.open(image_path)
    actual_w, actual_h = img.size
    api_w = result.get("image_width", actual_w)
    api_h = result.get("image_height", actual_h)

    if api_w != actual_w or api_h != actual_h:
        scale_x = actual_w / api_w
        scale_y = actual_h / api_h
        for part in result.get("parts", []):
            bbox = part["bbox"]
            part["bbox"] = [
                int(bbox[0] * scale_x),
                int(bbox[1] * scale_y),
                int(bbox[2] * scale_x),
                int(bbox[3] * scale_y),
            ]
        result["image_width"] = actual_w
        result["image_height"] = actual_h

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m autorig.vision <image_path>")
        sys.exit(1)

    result = analyze_image(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n파츠 {len(result.get('parts', []))}개 인식됨")
