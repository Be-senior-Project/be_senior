from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from generate_problem import generate_problem, GENERATION_MODEL
from verify_problem import verify_problem
from embed_problem import get_embedding, build_embed_text, EMBEDDING_MODEL
from db import init_db, save_problem

MAX_RETRIES = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)


class GenerateRequest(BaseModel):
    category: str
    difficulty: str
    language: str
    style: str
    count: int = Field(default=1, ge=1, le=10)


class GenerateResponse(BaseModel):
    requested: int
    saved: int
    failed: int
    problems: list[dict]


async def generate_verified_and_save(
    category: str,
    difficulty: str,
    language: str,
    style: str
) -> dict | None:
    for attempt in range(1, MAX_RETRIES + 1):
        problem = generate_problem(
            category=category,
            difficulty=difficulty,
            language=language,
            style=style
        )

        if problem is None:
            print(f"  [{attempt}/{MAX_RETRIES}] 생성 실패 (JSON 파싱 오류), 재시도...")
            continue

        if not verify_problem(problem):
            print(f"  [{attempt}/{MAX_RETRIES}] 검증 실패, 재시도...")
            continue

        # 임베딩 생성
        embed_text = build_embed_text(problem)
        embedding = get_embedding(embed_text)

        # DB 저장
        saved_id = await save_problem(
            category=category,
            difficulty=difficulty,
            language=language,
            style=style,
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

    print(f"\n총 {req.count}개 문제 생성 시작...")

    for i in range(req.count):
        print(f"\n[{i+1}/{req.count}] 생성 중... (카테고리: {req.category}, 난이도: {req.difficulty})")
        problem = await generate_verified_and_save(
            category=req.category,
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