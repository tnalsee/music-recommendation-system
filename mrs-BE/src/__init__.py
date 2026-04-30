from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging, time, json, os

from . import api
from .settings.config import AppConfig

# ── 로그 파일 및 폴더 설정 ─────────────────────────────
LOG_FILE_PATH = "E:/coconut2/logs/fastapi.log"
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# 1. 루트 로거는 터미널(콘솔)에만 찍히도록 설정 (파일 기록 X)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# 2. 미들웨어 전용 로거 생성
logger = logging.getLogger("fastapi_access")
logger.setLevel(logging.INFO)
logger.propagate = False  # 중요: 루트 로거로 로그가 전달되어 중복 기록되는 것을 방지

# 3. 전용 파일 핸들러 추가
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(message)s")) # JSON만 남기기 위해 메시지만 출력
logger.addHandler(file_handler)


# ── 미들웨어 함수 ───────────────────────────────────
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration,
        "client_ip": request.client.host if request.client else "unknown"
    }
    
    # 이제 이 로그는 오직 fastapi.log 파일에만 쌓입니다.
    logger.info(json.dumps(log_data, ensure_ascii=False))
    return response

# ── 앱 설정 ────────────────────────────────────────
config = AppConfig()
app = FastAPI()

app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)
app.include_router(api.router)