import os
import json
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def get_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "problems_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )


async def init_db():
    """테이블 초기화 (서버 시작 시 1회 실행)"""
    conn = await get_connection()
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id SERIAL PRIMARY KEY,
                category VARCHAR NOT NULL,
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


async def save_problem(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    problem_data: dict,
    embedding: list[float],
    generation_model: str,
    embedding_model: str
) -> int:
    """문제 저장 후 생성된 id 반환"""
    conn = await get_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO problems
                (category, difficulty, language, style, problem_data, generation_model, embedding_model, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            category,
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