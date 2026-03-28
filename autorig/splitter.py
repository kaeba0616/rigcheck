"""Step 2: 파츠 분리 — 바운딩 박스 크롭 + 텍스처 아틀라스 생성."""
from pathlib import Path

from PIL import Image


def split_parts(image_path: str | Path, parts_data: dict, output_dir: str | Path) -> dict:
    """이미지에서 파츠를 크롭하고 텍스처 아틀라스를 생성한다.

    Returns:
        atlas_info: {"atlas_path": str, "atlas_size": [w, h], "parts": [{name, uv: [x,y,w,h]}, ...]}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path).convert("RGBA")
    parts = parts_data.get("parts", [])

    # Step 1: 각 파츠를 크롭
    cropped_parts = []
    for part in parts:
        bbox = part["bbox"]
        # bbox 클램핑 (이미지 범위 초과 방지)
        x1 = max(0, bbox[0])
        y1 = max(0, bbox[1])
        x2 = min(img.width, bbox[2])
        y2 = min(img.height, bbox[3])

        if x2 <= x1 or y2 <= y1:
            continue

        cropped = img.crop((x1, y1, x2, y2))
        cropped_parts.append({
            "name": part["name"],
            "type": part["type"],
            "z_order": part.get("z_order", 0),
            "image": cropped,
            "original_bbox": [x1, y1, x2, y2],
        })

    # Step 2: bin-packing으로 텍스처 아틀라스 생성
    # 큰 파츠부터 배치 (면적 기준 내림차순)
    cropped_parts.sort(key=lambda p: p["image"].width * p["image"].height, reverse=True)

    ATLAS_SIZE = 2048
    PADDING = 4
    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))

    # 단순 row-based packing
    x_cursor = 0
    y_cursor = 0
    row_height = 0
    uv_map = []

    for part in cropped_parts:
        pw, ph = part["image"].size

        # 다음 행으로
        if x_cursor + pw + PADDING > ATLAS_SIZE:
            x_cursor = 0
            y_cursor += row_height + PADDING
            row_height = 0

        # 아틀라스 범위 초과
        if y_cursor + ph + PADDING > ATLAS_SIZE:
            break

        atlas.paste(part["image"], (x_cursor, y_cursor))

        uv_map.append({
            "name": part["name"],
            "type": part["type"],
            "z_order": part["z_order"],
            "uv": [x_cursor, y_cursor, pw, ph],
            "original_bbox": part["original_bbox"],
        })

        x_cursor += pw + PADDING
        row_height = max(row_height, ph)

    # 아틀라스 저장
    atlas_dir = output_dir / "model.4096"
    atlas_dir.mkdir(exist_ok=True)
    atlas_path = atlas_dir / "texture_00.png"
    atlas.save(atlas_path)

    return {
        "atlas_path": str(atlas_path),
        "atlas_size": [ATLAS_SIZE, ATLAS_SIZE],
        "parts": uv_map,
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m autorig.splitter <image_path> <parts_json_path> [output_dir]")
        sys.exit(1)

    with open(sys.argv[2]) as f:
        parts_data = json.load(f)

    output_dir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/autorig_output"
    result = split_parts(sys.argv[1], parts_data, output_dir)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n{len(result['parts'])}개 파츠 → 아틀라스 저장: {result['atlas_path']}")
