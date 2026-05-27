"""RAG 기반 문제 생성 파이프라인.

흐름:
  1. retrieve: 시드 DB에서 (category, subcategory, language) 필터 + 코사인 top-k
  2. generate: retrieve 결과를 컨텍스트로 끼워 rag_generator 호출 (temperature 0.4)
  3. verify: 기존 verifier/runners 재사용 — Docker 컴파일러/인터프리터로 코드 검증
  4. save: 통과 시 임베딩 후 problems 테이블에 저장

검증 실패 시 MAX_RETRIES 횟수만큼 generate부터 재시도 (retrieve는 첫 1회만, 결과 캐시).
시드 채움용은 app/services/problem_service_pipeline.py 그대로 사용.
"""

from typing import Optional
import asyncio

from app.core.enums import Category, AlgorithmSubcategory, Difficulty, Language, Style
from app.core.config import MAX_RETRIES, GENERATION_MODEL, EMBEDDING_MODEL

from app.services.retriever import retrieve_similar_problems
from app.services.rag_generator import generate_problem_with_rag
from app.services.verifier import verify_problem
from app.services.embedder import build_embed_text, get_embedding
from app.repositories.problem_repo import save_problem


""" RAG 파이프라인: retrieve → generate → verify → (옵션) save. 실패 시 None 반환 """
async def generate_with_rag_and_save(
    index: int,
    total: int,
    category: Category,
    subcategory: Optional[AlgorithmSubcategory],
    difficulty: Difficulty,
    language: Language,
    style: Style,
    save: bool = True,
) -> Optional[dict]:

    tag = f"[{index}/{total}]"

    # 1. retrieve는 쿼리가 동일하므로 첫 1회만 실행하고 재시도 시 재사용
    try:
        examples = await retrieve_similar_problems(
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value,
        )
    except Exception as e:
        # retrieve 실패는 RAG 전체를 막을 정도는 아님 — 빈 예시로 폴백
        print(f"  {tag} retrieve 실패, 예시 없이 진행: {e}")
        examples = []

    print(f"  {tag} retrieve 완료: 시드 {len(examples)}개 컨텍스트로 사용")

    # 2~4. MAX_RETRIES 횟수만큼 generate + verify
    for attempt in range(1, MAX_RETRIES + 1):
        # 2. 생성
        problem = await asyncio.to_thread(
            generate_problem_with_rag,
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value,
            examples=examples,
        )

        if problem is None:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 생성 실패 (JSON 파싱 오류), 재시도...")
            continue

        # 3. 검증 (subprocess 호출 → 동기 → to_thread)
        result = await asyncio.to_thread(verify_problem, problem, language.value)
        if not result["ok"]:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 검증 실패 [{result['reason']}]: {result['detail']}")
            continue

        # 4. 임베딩 + 저장
        embed_text = build_embed_text(problem)
        embedding = await asyncio.to_thread(get_embedding, embed_text)

        if save:
            saved_id = await save_problem(
                category=category.value,
                subcategory=subcategory.value if subcategory else None,
                difficulty=difficulty.value,
                language=language.value,
                style=style.value,
                problem_data=problem,
                embedding=embedding,
                generation_model=GENERATION_MODEL,
                embedding_model=EMBEDDING_MODEL,
            )
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 검증 통과 → DB 저장 완료 (id: {saved_id})")
        else:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 검증 통과 (저장 생략)")
        return problem

    print(f"  {tag} {MAX_RETRIES}회 재시도 후 실패, 제외됨")
    return None
