
from app.core.enums import Category, AlgorithmSubcategory, Difficulty, Language, Style   # Enum 정의 (카테고리, 난이도, 언어, 스타일)
from typing import Optional # 타입 힌트
import asyncio  # 비동기 병렬 처리

from app.services.generator import generate_problem
from app.services.verifier import verify_problem
from app.services.embedder import build_embed_text, get_embedding
from app.repositories.problem_repo import save_problem

from app.core.config import MAX_RETRIES, GENERATION_MODEL, EMBEDDING_MODEL

""" 문제 생성, 검증, 저장. 실패 시 None 반환 """
async def generate_verified_and_save(
    index: int,
    total: int,
    category: Category,
    subcategory: Optional[AlgorithmSubcategory],
    difficulty: Difficulty,
    language: Language,
    style: Style,
    save: bool,
) -> Optional[dict]:
    
    tag = f"[{index}/{total}]"
    # MAX_RETRIES 횟수만큼 문제 생성 및 검증
    for attempt in range(1, MAX_RETRIES + 1):
        # generate_problem은 동기 함수라 다른 코루틴을 막지 않게 별도 스레드에서 실행
        problem = await asyncio.to_thread(
            generate_problem,
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value,
        )

        # 문제가 없을 경우 다시 문제 생성 시도(최대 MAX_RETRIES만큼 실행)
        if problem is None:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 생성 실패 (JSON 파싱 오류), 재시도...")
            continue

        # 코드 실행/검증 (내부적으로 subprocess 호출 → 동기라 to_thread 사용)
        result = await asyncio.to_thread(verify_problem, problem, language.value)
        if not result["ok"]:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 검증 실패 [{result['reason']}]: {result['detail']}")
            continue

        # 임베딩 입력 텍스트 조립
        embed_text = build_embed_text(problem)

        # 임베딩
        embedding = await asyncio.to_thread(get_embedding, embed_text)

        if save:
            # 문제 저장
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