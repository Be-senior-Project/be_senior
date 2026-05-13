import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

from generate_problem import generate_problem, GENERATION_MODEL
from verify_problem import verify_problem
from embed_problem import get_embedding, build_embed_text, EMBEDDING_MODEL
from db import init_db, save_problem
from enums import Category, AlgorithmSubcategory, Difficulty, Language, Style

load_dotenv()

MAX_RETRIES = 3
MAX_COUNT = int(os.getenv("MAX_COUNT", "50"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "10"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)


class GenerateRequest(BaseModel):
    category: Category
    subcategory: Optional[AlgorithmSubcategory] = None
    difficulty: Difficulty
    language: Language
    style: Style
    count: int = Field(default=1, ge=1, le=MAX_COUNT)

    @model_validator(mode="after")
    def validate_subcategory(self):
        if self.category == Category.basic and self.subcategory is not None:
            raise ValueError("Basic/Introductory 카테고리는 중단원을 지정할 수 없습니다.")
        return self


class GenerateResponse(BaseModel):
    requested: int
    saved: int
    failed: int
    problems: list[dict]


async def generate_verified_and_save(
    index: int,
    total: int,
    category: Category,
    subcategory: Optional[AlgorithmSubcategory],
    difficulty: Difficulty,
    language: Language,
    style: Style,
) -> Optional[dict]:
    """단일 문제 생성 + 검증 + 저장. 실패 시 None 반환."""
    tag = f"[{index}/{total}]"
    for attempt in range(1, MAX_RETRIES + 1):
        # GPT 호출은 동기 SDK이므로 to_thread 로 다른 작업과 진짜 병렬화
        problem = await asyncio.to_thread(
            generate_problem,
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value,
        )

        if problem is None:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 생성 실패 (JSON 파싱 오류), 재시도...")
            continue

        # 검증도 subprocess(compile/run) 호출이라 동기 → to_thread 로
        result = await asyncio.to_thread(verify_problem, problem, language.value)
        if not result["ok"]:
            print(f"  {tag} [{attempt}/{MAX_RETRIES}] 검증 실패 [{result['reason']}]: {result['detail']}")
            continue

        embed_text = build_embed_text(problem)
        embedding = await asyncio.to_thread(get_embedding, embed_text)

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
        return problem

    print(f"  {tag} {MAX_RETRIES}회 재시도 후 실패, 제외됨")
    return None


@app.post("/generate", response_model=GenerateResponse)
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