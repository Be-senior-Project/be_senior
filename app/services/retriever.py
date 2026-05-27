"""RAG retriever.

사용자 /generate 요청을 받아 시드 DB에서 가장 유사한 top-k 문제를 가져온다.

흐름:
  1. 요청 enum 값들을 짧은 자연어 쿼리로 합성
  2. get_embedding으로 쿼리 벡터화 (시드와 동일한 임베딩 모델 사용)
  3. (category, subcategory, language) SQL 필터 + 쿼리 벡터로 코사인 top-k 검색
  4. problem_data(JSONB) 리스트 반환 → 프롬프트에 끼울 raw 문제 dict
"""

import asyncio
import json
from typing import Optional

from app.repositories.problem_repo import get_connection
from app.services.embedder import get_embedding
from app.core.config import RAG_TOP_K


""" 쿼리 텍스트 합성

build_embed_text가 자연어 위주이므로, 쿼리도 비슷한 형태로 만들어야 임베딩 공간이 맞물린다.
요청에 들어있는 정보(category/subcategory/difficulty/language/style)만으로 짧게 구성.
"""
def _build_query_text(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    subcategory: Optional[str] = None,
) -> str:
    topic = subcategory if subcategory else category
    return "\n".join([
        f"Topic: {topic}",
        f"Category: {category}",
        f"Language: {language}",
        f"Difficulty: {difficulty}",
        f"Style: {style}",
    ])


""" 시드 DB에서 유사한 문제 top-k retrieve

Returns:
    list[dict]: problem_data(JSONB)를 dict로 파싱한 리스트. 매칭 결과가 없으면 빈 리스트.
"""
async def retrieve_similar_problems(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    subcategory: Optional[str] = None,
    top_k: int = RAG_TOP_K,
) -> list[dict]:
    # 1. 쿼리 텍스트 합성
    query_text = _build_query_text(category, difficulty, language, style, subcategory)

    # 2. 쿼리 임베딩 (get_embedding은 동기 → 이벤트 루프 막지 않게 별도 스레드)
    query_embedding = await asyncio.to_thread(get_embedding, query_text)

    # 3. SQL 필터 + 코사인 검색 (HNSW 인덱스 활용)
    conn = await get_connection()
    try:
        if subcategory is None:
            rows = await conn.fetch("""
                SELECT problem_data
                FROM problems
                WHERE category = $1
                  AND subcategory IS NULL
                  AND language = $2
                ORDER BY embedding <=> $3
                LIMIT $4
            """, category, language, query_embedding, top_k)
        else:
            rows = await conn.fetch("""
                SELECT problem_data
                FROM problems
                WHERE category = $1
                  AND subcategory = $2
                  AND language = $3
                ORDER BY embedding <=> $4
                LIMIT $5
            """, category, subcategory, language, query_embedding, top_k)
    finally:
        await conn.close()

    # 4. JSONB → dict 파싱 (asyncpg는 기본적으로 jsonb를 문자열로 반환)
    results: list[dict] = []
    for row in rows:
        data = row["problem_data"]
        if isinstance(data, str):
            data = json.loads(data)
        results.append(data)
    return results
