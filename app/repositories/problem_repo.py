import os
import json
from typing import Optional
import asyncpg # 비동기로 postgreSQL 처리해주는 라이브러리
from pgvector.asyncpg import register_vector # vector 타입 ↔ list[float] 자동 변환
from dotenv import load_dotenv # .env 환경 변수 파일을 가져올 수 있게 해주는 라이브러리

# 환경 변수에 .env 파일을 참조하여 환경 변수 설정
load_dotenv()


# pgvector codec 등록 없이 raw conn 생성 (init_db 내부에서 extension 깔기 전에 사용)
async def _create_raw_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "problems_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )


# 일반 작업용 conn (vector codec 등록 포함). init_db 이후 호출되어야 안전.
async def get_connection():
    conn = await _create_raw_connection()
    await register_vector(conn)
    return conn


# DB 테이블/인덱스 초기화
async def init_db():
    conn = await _create_raw_connection() # extension 아직 없을 수 있으므로 raw conn
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector") # pgvector extension 활성화
        await register_vector(conn) # extension 활성화 직후 코덱 등록(이 conn에서 vector 컬럼은 안 다루지만 일관성)

        # 문제 테이블 (시드/생성본 구분 없이 모든 row가 시드 역할)
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

        # RAG retrieve용 cosine 유사도 ANN 인덱스 (HNSW)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS problems_embedding_cosine_idx
            ON problems USING hnsw (embedding vector_cosine_ops)
        """)

        # 시드 카운트/필터 조회용 보조 인덱스
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS problems_filter_idx
            ON problems (category, subcategory, language)
        """)
    finally:
        await conn.close()


"""주어진 (category, subcategory, language) 조합의 시드 문제 수 카운트.

/generate에서 RAG 모드/시드 채움 모드 분기 판단용.
0이면 시드 채움 모드(prompt-only), 1 이상이면 RAG 모드.
"""
async def count_seeds(
    category: str,
    language: str,
    subcategory: Optional[str] = None,
) -> int:
    conn = await get_connection()
    try:
        if subcategory is None:
            row = await conn.fetchrow("""
                SELECT COUNT(*) AS n
                FROM problems
                WHERE category = $1
                  AND subcategory IS NULL
                  AND language = $2
            """, category, language)
        else:
            row = await conn.fetchrow("""
                SELECT COUNT(*) AS n
                FROM problems
                WHERE category = $1
                  AND subcategory = $2
                  AND language = $3
            """, category, subcategory, language)
        return row["n"]
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
            embedding,  # pgvector codec이 list[float] → vector(1536)로 직렬화
        )
        return row["id"]
    finally:
        await conn.close()
