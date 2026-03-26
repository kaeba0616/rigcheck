# RigCheck

Live2D 리깅 QA 자동화 도구. runtime JSON 파일을 분석해서 리깅 품질 문제를 자동으로 감지합니다.

## 검사 항목 (8개 규칙)

| 규칙 | 검사 내용 | 심각도 |
|------|----------|--------|
| 좌우 대칭성 | L/R 파라미터/파츠 쌍 매칭 | Warning |
| 필수 그룹 | EyeBlink, LipSync 존재 여부 | Critical |
| 물리 설정 | FPS, 중력, 정규화 범위, 개수 정합성 | Warning |
| 표정 파라미터 | 참조 유효성, 값 범위, Blend 모드 | Warning |
| 그룹 일관성 | 미지정/빈 그룹, 잘못된 참조 | Info~Warning |
| 네이밍 규칙 | 접두사, 중복 ID, 특수문자 | Info~Warning |
| 미사용 노드 | 어디서도 참조 안 되는 파라미터 감지 | Info~Warning |
| 파라미터 조합 | CombinedParameters 유효성, Blend 충돌 | Info~Warning |

## 빠른 시작

### CLI

```bash
python3 -m rigcheck ./your_model/runtime
```

### 웹 UI

```bash
# 가상환경 설정
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-multipart

# 서버 시작
python3 -m server
```

http://localhost:8000 에서 runtime 폴더를 ZIP으로 압축해서 업로드하세요.

## 입력 형식

Live2D Cubism의 **runtime 폴더**를 ZIP으로 압축:

```
runtime/
├── model_name.model3.json    (필수)
├── model_name.cdi3.json      (파라미터/파츠 정보)
├── model_name.physics3.json  (물리 설정)
├── expressions/              (표정 파일)
│   └── *.exp3.json
└── motions/                  (모션 파일)
    └── *.motion3.json
```

## 테스트

```bash
python3 -m tests.test_rules
```

## 기술 스택

- Python 3.12+
- FastAPI (백엔드)
- 순수 HTML/CSS/JS (프론트엔드, 빌드 도구 없음)
- 외부 AI/ML 의존성 없음 (규칙 기반)
