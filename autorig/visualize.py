"""파츠 인식 결과를 시각화 — 바운딩 박스를 이미지 위에 그린다."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "eye": "#ef4444",
    "eyebrow": "#f97316",
    "mouth": "#eab308",
    "nose": "#84cc16",
    "face": "#22c55e",
    "hair": "#06b6d4",
    "ear": "#8b5cf6",
    "neck": "#a855f7",
    "body": "#3b82f6",
    "arm": "#ec4899",
}


def visualize(image_path: str, parts_data: dict, output_path: str = None):
    """이미지 위에 바운딩 박스를 그려서 저장한다."""
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for part in parts_data.get("parts", []):
        bbox = part["bbox"]
        color = COLORS.get(part["type"], "#ffffff")
        name = part["name"]
        z = part.get("z_order", 0)

        # 반투명 박스
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        draw.rectangle(bbox, outline=color, width=2)
        draw.rectangle(bbox, fill=(r, g, b, 40))

        # 라벨
        label = f"{name} (z:{z})"
        draw.text((bbox[0] + 2, bbox[1] - 12), label, fill=color)

    result = Image.alpha_composite(img, overlay)

    if output_path is None:
        output_path = str(Path(image_path).stem) + "_parts.png"

    result.save(output_path)
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m autorig.visualize <image_path> <parts_json_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    with open(sys.argv[2]) as f:
        parts_data = json.load(f)

    visualize(image_path, parts_data)
