"""RigCheck FastAPI 서버."""
import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from rigcheck.engine import run_check
from autorig.pipeline import run_pipeline

RULE_DESCRIPTIONS = {
    "좌우 대칭성 검사": "L/R로 나뉘는 파라미터와 파츠가 짝이 맞는지 확인합니다.",
    "필수 그룹 검사": "VTuber 트래킹에 필수적인 EyeBlink, LipSync 그룹이 있는지 확인합니다.",
    "물리 설정 검증": "머리카락, 옷 등 물리 시뮬레이션 설정이 정상인지 확인합니다.",
    "표정 파라미터 검사": "표정 파일의 파라미터 참조와 값이 유효한지 확인합니다.",
    "파라미터 그룹 일관성": "파라미터가 올바른 그룹에 배정되어 있는지 확인합니다.",
    "네이밍 규칙 검사": "파라미터/파츠 ID가 Live2D 표준 규칙을 따르는지 확인합니다.",
    "미사용 노드 감지": "어디에서도 사용되지 않는 파라미터나 파츠를 찾습니다.",
    "파라미터 조합 검사": "파라미터 조합 설정과 표정 간 Blend 모드 충돌을 확인합니다.",
    "모션 키프레임 분석": "모션 데이터에서 급격한 값 변화(부자연스러운 움직임)를 감지합니다.",
    "표정 조합 스트레스 테스트": "모든 표정을 동시에 적용했을 때 파라미터가 극단으로 가는지 시뮬레이션합니다.",
    "물리 체인 검증": "물리 설정의 입력→출력 체인에서 순환(무한루프)이나 끊어진 연결을 찾습니다.",
    "파일 참조 무결성": "model3.json에서 참조하는 텍스처, 모션, 표정 파일이 실제로 존재하는지 확인합니다.",
}

app = FastAPI(title="RigCheck", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/check")
async def check_model(file: UploadFile = File(...)):
    """Live2D runtime 파일을 검사한다. ZIP 또는 개별 JSON 파일 지원."""
    content = await file.read()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        if file.filename and file.filename.endswith(".zip"):
            # ZIP 파일 — runtime 폴더 구조 전체
            with zipfile.ZipFile(BytesIO(content)) as zf:
                zf.extractall(tmp)

            # model3.json 찾기 — 최상위 또는 서브디렉토리
            model3_files = list(tmp.rglob("*.model3.json"))
            if not model3_files:
                return JSONResponse(
                    status_code=400,
                    content={"error": "ZIP 안에 .model3.json 파일이 없습니다."},
                )
            runtime_dir = str(model3_files[0].parent)
        else:
            # 개별 JSON 파일 — 단일 파일 검사는 지원 불가, ZIP 안내
            return JSONResponse(
                status_code=400,
                content={"error": "runtime 폴더를 ZIP으로 압축해서 업로드하세요."},
            )

        try:
            report = run_check(runtime_dir)
        except FileNotFoundError as e:
            return JSONResponse(status_code=400, content={"error": str(e)})

    # 전체 판정
    if report.critical_count > 0:
        verdict = "수정이 필요합니다"
        verdict_type = "critical"
    elif report.warning_count > 0:
        verdict = "개선할 부분이 있습니다"
        verdict_type = "warning"
    else:
        verdict = "이 모델은 양호합니다"
        verdict_type = "pass"

    return {
        "model_name": report.model_name,
        "verdict": verdict,
        "verdict_type": verdict_type,
        "total_findings": report.total_findings,
        "critical_count": report.critical_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "results": [
            {
                "rule_name": r.rule_name,
                "description": RULE_DESCRIPTIONS.get(r.rule_name, ""),
                "passed": r.passed,
                "findings": [
                    {
                        "severity": f.severity.value,
                        "message": f.message,
                        "details": f.details,
                    }
                    for f in r.findings
                ],
            }
            for r in report.results
        ],
    }


@app.post("/api/autorig")
async def autorig(file: UploadFile = File(...)):
    """이미지에서 Live2D 모델을 자동 생성한다."""
    content = await file.read()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # 이미지 저장
        ext = Path(file.filename or "image.png").suffix or ".png"
        image_path = tmp / f"input{ext}"
        image_path.write_bytes(content)

        output_dir = tmp / "output"

        try:
            result = run_pipeline(str(image_path), str(output_dir))
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

        if result["parts_count"] == 0:
            return JSONResponse(status_code=400, content={"error": "파츠를 인식하지 못했습니다."})

        # output 폴더를 ZIP으로 패키징
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname)
        zip_bytes = zip_buffer.getvalue()

        # 파츠 데이터에서 프리뷰용 정보 추출
        import base64
        parts_for_preview = []
        atlas_info_path = output_dir / "atlas_info.json"
        if atlas_info_path.exists():
            with open(atlas_info_path) as f:
                atlas_info = json.load(f)
                parts_for_preview = atlas_info.get("parts", [])

        # 아틀라스 이미지를 base64로
        atlas_path = output_dir / "model.4096" / "texture_00.png"
        atlas_b64 = ""
        if atlas_path.exists():
            atlas_b64 = base64.b64encode(atlas_path.read_bytes()).decode()

        # 원본 이미지 + 파츠 오버레이 프리뷰
        from autorig.visualize import visualize
        preview_path = tmp / "preview.png"
        visualize(str(image_path), result["parts_data"], str(preview_path))
        preview_b64 = base64.b64encode(preview_path.read_bytes()).decode()

    return {
        "parts_count": result["parts_count"],
        "parts": parts_for_preview,
        "parts_data": result["parts_data"],
        "preview_image": preview_b64,
        "atlas_image": atlas_b64,
        "zip_base64": base64.b64encode(zip_bytes).decode(),
        "qa_report": result["qa_report"],
    }


# 정적 파일 서빙 (web/index.html)
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    @app.get("/")
    async def index():
        return FileResponse(WEB_DIR / "autorig.html")

    @app.get("/check")
    async def check_page():
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
