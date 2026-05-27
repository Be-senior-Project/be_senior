from contextlib import asynccontextmanager  # DB 초기화용 lifespan 데코레이터
from fastapi import FastAPI # API 서버 프레임워크
from dotenv import load_dotenv  # .env 파일에서 환경변수 로드

from app.repositories.problem_repo import init_db    # DB 초기화 함수
from app.api import generate    # /generate 라우터

load_dotenv() # .env 파일에서 환경변수 로드


# 서버 시작/종료 시 한 번씩 실행할 동작 지정 (yield 앞=시작, 뒤=종료). 현재는 시작 시 DB 초기화만 수행.
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# FastAPI 서버 실행
app = FastAPI(lifespan=lifespan)
app.include_router(generate.router)
