from fastapi import APIRouter # FastAPI 라우터
import asyncio  # 비동기 병렬 처리
from typing import Optional # 타입 힌트


from app.services.problem_service_pipeline import generate_verified_and_save  # 시드 채움 모드(prompt-only)
from app.services.rag_problem_pipeline import generate_with_rag_and_save      # RAG 모드
from app.repositories.problem_repo import count_seeds                          # 시드 존재 여부 체크
from app.schemas.request import GenerateResponse, GenerateRequest
from app.core.config import MAX_CONCURRENT

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    category_str = req.category.value
    if req.subcategory:
        category_str += f" - {req.subcategory.value}"

    # 시드 존재 여부 체크 → 모드 결정
    seed_count = await count_seeds(
        category=req.category.value,
        subcategory=req.subcategory.value if req.subcategory else None,
        language=req.language.value,
    )
    use_rag = seed_count > 0
    mode_label = "RAG" if use_rag else "SEED (prompt-only)"
    pipeline = generate_with_rag_and_save if use_rag else generate_verified_and_save

    print(
        f"\n총 {req.count}개 문제 생성 시작..."
        f" (카테고리: {category_str}, 난이도: {req.difficulty.value},"
        f" 언어: {req.language.value}, 모드: {mode_label},"
        f" 기존 시드: {seed_count}개, 동시 실행: 최대 {MAX_CONCURRENT}개)"
    )

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_one(i: int) -> Optional[dict]:
        async with sem:
            return await pipeline(
                index=i + 1,
                total=req.count,
                category=req.category,
                subcategory=req.subcategory,
                difficulty=req.difficulty,
                language=req.language,
                style=req.style,
                save=True,
            )

    results = await asyncio.gather(*(run_one(i) for i in range(req.count)))

    problems = [r for r in results if r is not None]
    saved = len(problems)
    failed = req.count - saved

    print(f"\n완료: {req.count}개 요청 → {saved}개 저장, {failed}개 제외 (모드: {mode_label})")

    return GenerateResponse(
        requested=req.count,
        saved=saved,
        failed=failed,
        problems=problems,
    )
