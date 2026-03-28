"""AutoRig 파이프라인 — 이미지 → 파츠 인식 → 분리 → JSON 생성 → QA."""
import json
import shutil
from pathlib import Path

from .vision import analyze_image
from .splitter import split_parts
from .generator import generate_runtime


def run_pipeline(image_path: str | Path, output_dir: str | Path = None) -> dict:
    """이미지 한 장에서 Live2D runtime 폴더를 생성한다.

    Returns:
        {"output_dir": str, "parts_count": int, "qa_report": str, "parts_data": dict}
    """
    image_path = Path(image_path)
    if output_dir is None:
        output_dir = Path("/tmp/autorig_output")

    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Step 1: 파츠 인식
    print("[Step 1/4] Grok Vision으로 파츠 인식 중...")
    parts_data = analyze_image(image_path)
    parts_count = len(parts_data.get("parts", []))
    print(f"  → {parts_count}개 파츠 인식됨")

    if parts_count == 0:
        return {
            "output_dir": str(output_dir),
            "parts_count": 0,
            "qa_report": "파츠를 인식하지 못했습니다.",
            "parts_data": parts_data,
        }

    # Step 2: 파츠 분리 + 텍스처 아틀라스
    print("[Step 2/4] 파츠 분리 + 텍스처 아틀라스 생성 중...")
    atlas_info = split_parts(image_path, parts_data, output_dir)
    print(f"  → 아틀라스 저장: {atlas_info['atlas_path']}")

    # Step 3: Live2D JSON 생성
    print("[Step 3/4] Live2D runtime JSON 생성 중...")
    generate_runtime(image_path, atlas_info, output_dir)
    print(f"  → model3.json, cdi3.json 생성 완료")

    # Step 4: RigCheck QA
    print("[Step 4/4] RigCheck QA 검증 중...")
    try:
        from rigcheck.engine import run_check
        report = run_check(str(output_dir))
        qa_summary = report.summary()
        print(f"  → 검사 완료: {report.total_findings}건 발견 "
              f"(Critical: {report.critical_count}, "
              f"Warning: {report.warning_count}, "
              f"Info: {report.info_count})")
    except Exception as e:
        qa_summary = f"QA 실행 실패: {e}"
        print(f"  → QA 실패: {e}")

    # parts_data 저장 (디버깅용)
    with open(output_dir / "parts_data.json", "w", encoding="utf-8") as f:
        json.dump(parts_data, f, indent=2, ensure_ascii=False)

    with open(output_dir / "atlas_info.json", "w", encoding="utf-8") as f:
        json.dump(atlas_info, f, indent=2, ensure_ascii=False)

    return {
        "output_dir": str(output_dir),
        "parts_count": parts_count,
        "qa_report": qa_summary,
        "parts_data": parts_data,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m autorig.pipeline <image_path> [output_dir]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result = run_pipeline(image_path, output_dir)
    print(f"\n{'='*50}")
    print(f"완료! 파츠 {result['parts_count']}개 → {result['output_dir']}")
    print(f"\nQA 리포트:")
    print(result["qa_report"])
