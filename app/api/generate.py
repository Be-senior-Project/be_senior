from fastapi import APIRouter # FastAPI 라우터
import asyncio  # 비동기 병렬 처리
from typing import Optional # 타입 힌트


from app.services.problem_service_pipeline import generate_verified_and_save
from app.schemas.request import GenerateResponse, GenerateRequest
from app.core.config import MAX_CONCURRENT

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    category_str = req.category.value
    if req.subcategory:
        category_str += f" - {req.subcategory.value}"

    print(
        f"\n총 {req.count}개 문제 생성 시작..."
        f" (카테고리: {category_str}, 난이도: {req.difficulty.value},"
        f" 언어: {req.language.value}, 동시 실행: 최대 {MAX_CONCURRENT}개)"
    )

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_one(i: int) -> Optional[dict]:
        async with sem:
            return await generate_verified_and_save(
                index=i + 1,
                total=req.count,
                category=req.category,
                subcategory=req.subcategory,
                difficulty=req.difficulty,
                language=req.language,
                style=req.style,
            )

    results = await asyncio.gather(*(run_one(i) for i in range(req.count)))

    problems = [r for r in results if r is not None]
    saved = len(problems)
    failed = req.count - saved

    print(f"\n완료: {req.count}개 요청 → {saved}개 저장, {failed}개 제외")

    return GenerateResponse(
        requested=req.count,
        saved=saved,
        failed=failed,
        problems=problems,
    )

