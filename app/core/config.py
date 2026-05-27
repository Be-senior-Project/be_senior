import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MAX_RETRIES = 3 # 문제 생성/검증 최대 재시도 횟수
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "10")) # 문제 생성/검증 동시 실행 최대 개수 (서버 과부하 방지용, 입력값 검증에도 사용)
MAX_COUNT = int(os.getenv("MAX_COUNT", "50")) # 한 번에 생성 요청할 수 있는 최대 문제 수 (입력값 검증에도 사용)


PROMPTS_DIR = BASE_DIR/ "prompts"
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gpt-5.4-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# RAG retrieve 시 컨텍스트로 끼울 시드 문제 개수
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
# RAG generator 호출 시 temperature
RAG_TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.4"))
