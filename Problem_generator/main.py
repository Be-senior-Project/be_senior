from contextlib import asynccontextmanager
from typing import Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from generate_problem import generate_problem, GENERATION_MODEL
from verify_problem import verify_problem
from embed_problem import get_embedding, build_embed_text, EMBEDDING_MODEL
from db import init_db, save_problem
from enums import Category, AlgorithmSubcategory, SQLSubcategory, Difficulty, Language, Style

MAX_RETRIES = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)


class GenerateRequest(BaseModel):
    category: Category
    subcategory: Optional[Union[AlgorithmSubcategory, SQLSubcategory]] = None
    difficulty: Difficulty
    language: Language
    style: Style
    count: int = Field(default=1, ge=1, le=10)

    @model_validator(mode="after")
    def validate_subcategory(self):
        if self.category == Category.basic and self.subcategory is not None:
            raise ValueError("Basic/Introductory 카테고리는 중단원을 지정할 수 없습니다.")
        if self.category == Category.algorithm and self.subcategory is not None:
            if not isinstance(self.subcategory, AlgorithmSubcategory):
                raise ValueError("Algorithm/Data Structure 카테고리는 AlgorithmSubcategory만 지정할 수 있습니다.")
        if self.category == Category.sql and self.subcategory is not None:
            if not isinstance(self.subcategory, SQLSubcategory):
                raise ValueError("SQL 카테고리는 SQLSubcategory만 지정할 수 있습니다.")
        return self


class GenerateResponse(BaseModel):
    requested: int
    saved: int
    failed: int
    problems: list[dict]


async def generate_verified_and_save(
    category: Category,
    subcategory: Optional[Union[AlgorithmSubcategory, SQLSubcategory]],
    difficulty: Difficulty,
    language: Language,
    style: Style
) -> dict | None:
    for attempt in range(1, MAX_RETRIES + 1):
        problem = generate_problem(
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value
        )

        if problem is None:
            print(f"  [{attempt}/{MAX_RETRIES}] 생성 실패 (JSON 파싱 오류), 재시도...")
            continue

        if not verify_problem(problem):
            print(f"  [{attempt}/{MAX_RETRIES}] 검증 실패, 재시도...")
            continue

        embed_text = build_embed_text(problem)
        embedding = get_embedding(embed_text)

        saved_id = await save_problem(
            category=category.value,
            subcategory=subcategory.value if subcategory else None,
            difficulty=difficulty.value,
            language=language.value,
            style=style.value,
            problem_data=problem,
            embedding=embedding,
            generation_model=GENERATION_MODEL,
            embedding_model=EMBEDDING_MODEL
        )

        print(f"  [{attempt}/{MAX_RETRIES}] 검증 통과 → DB 저장 완료 (id: {saved_id})")
        return problem

    print(f"  {MAX_RETRIES}회 재시도 후 실패, 제외됨")
    return None


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    problems = []
    failed = 0

    category_str = req.category.value
    if req.subcategory:
        category_str += f" - {req.subcategory.value}"

    print(f"\n총 {req.count}개 문제 생성 시작...")

    for i in range(req.count):
        print(f"\n[{i+1}/{req.count}] 생성 중... (카테고리: {category_str}, 난이도: {req.difficulty.value})")
        problem = await generate_verified_and_save(
            category=req.category,
            subcategory=req.subcategory,
            difficulty=req.difficulty,
            language=req.language,
            style=req.style
        )

        if problem:
            problems.append(problem)
        else:
            failed += 1

    saved = len(problems)
    print(f"\n완료: {req.count}개 요청 → {saved}개 저장, {failed}개 제외")

    return GenerateResponse(
        requested=req.count,
        saved=saved,
        failed=failed,
        problems=problems
    )