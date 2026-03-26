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

    return {
        "model_name": report.model_name,
        "total_findings": report.total_findings,
        "critical_count": report.critical_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "results": [
            {
                "rule_name": r.rule_name,
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


# 정적 파일 서빙 (web/index.html)
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    @app.get("/")
    async def index():
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
