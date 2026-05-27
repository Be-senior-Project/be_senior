import os
import json
from typing import Optional
import asyncpg # 비동기로 postgreSQL 처리해주는 라이브러리
from dotenv import load_dotenv # .env 환경 변수 파일을 가져올 수 있게 해주는 라이브러리

# 환경 변수에 .env 파일을 참조하여 환경 변수 설정
load_dotenv()


# postgreSQL DB와 연결
async def get_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "problems_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )


# DB 테이블 초기화
async def init_db():
    conn = await get_connection() # DB와 연결
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector") # pgvector table 없을 시 생성
        # table 없을 경우 생성
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id SERIAL PRIMARY KEY,
                category VARCHAR NOT NULL,
                subcategory VARCHAR,
                difficulty VARCHAR NOT NULL,
                language VARCHAR NOT NULL,
                style VARCHAR NOT NULL,
                problem_data JSONB NOT NULL,
                generation_model VARCHAR NOT NULL,
                embedding_model VARCHAR NOT NULL,
                embedding vector(1536),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    finally:
        await conn.close()


"""문제 저장 후 생성된 id 반환"""
async def save_problem(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    problem_data: dict,
    embedding: list[float],
    generation_model: str,
    embedding_model: str,
    subcategory: Optional[str] = None
) -> int:
    conn = await get_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO problems
                (category, subcategory, difficulty, language, style, problem_data, generation_model, embedding_model, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
            category,
            subcategory,
            difficulty,
            language,
            style,
            json.dumps(problem_data, ensure_ascii=False),
            generation_model,
            embedding_model,
            str(embedding)
        )
        return row["id"]
    finally:
        await conn.close()