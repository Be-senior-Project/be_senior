"""RAG 기반 문제 생성기.

흐름:
  1. retriever가 가져온 시드 문제 리스트(top-k)를 받음
  2. 예시들을 프롬프트에 끼울 수 있는 텍스트 블록으로 포맷 (토큰 절약 위해 핵심 필드만)
  3. user_prompt_rag.md에 {examples} 슬롯과 요청 정보를 채워 OpenAI 호출
  4. temperature는 RAG_TEMPERATURE(기본 0.4), JSON 모드 강제
  5. 응답 JSON 파싱 후 dict 반환 (실패 시 None)

prompt-only 버전(app/services/generator.py)과 분리해서 둠.
시드 채울 때는 generator.generate_problem(), RAG 생성 시에는 이 모듈 사용.
"""

import json
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from app.core.config import PROMPTS_DIR, GENERATION_MODEL, RAG_TEMPERATURE

load_dotenv()


def _get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일 또는 환경변수를 확인하세요.")
    return OpenAI()


""" 프롬프트 md 파일 로더 (generator.py와 동일 구현, 의도적 중복) """
def _load_prompt(filename: str, **kwargs) -> str:
    prompt = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return prompt.format(**kwargs) if kwargs else prompt


""" retriever 결과 → 프롬프트에 끼울 예시 블록 텍스트

토큰 절약을 위해 핵심 필드만 추린다.
포함:  Type, Title, Description, Constraints, Signature, IO Example
제외:  Concept Explanation, Explanation, Code Skeleton, Answer
       (스타일/구조 참고용으로는 위 6개로 충분, 풀이 정보까지 주면 베끼기 유도됨)
"""
def _format_examples(examples: list[dict]) -> str:
    if not examples:
        return "(시드 DB에서 검색된 예시가 없습니다. 일반 지침에 따라 생성하세요.)"

    blocks = []
    for i, ex in enumerate(examples, start=1):
        prob = ex.get("Problem", {})
        compact = {
            "Type": prob.get("Type"),
            "Title": prob.get("Title"),
            "Description": prob.get("Description"),
            "Constraints": prob.get("Constraints", []) or [],
            "Signature": prob.get("Signature"),
            "IO Example": prob.get("IO Example"),
        }
        blocks.append(
            f"### Example {i}\n"
            f"```json\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n```"
        )
    return "\n\n".join(blocks)


""" RAG 기반 문제 생성 """
def generate_problem_with_rag(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    examples: list[dict],
    subcategory: Optional[str] = None,
) -> Optional[dict]:

    # OpenAI 클라이언트
    client = _get_client()

    # retrieve 결과 → 텍스트 블록
    examples_text = _format_examples(examples)

    # system은 공통, user는 RAG 전용 프롬프트
    system_prompt = _load_prompt("system_prompt.md")
    user_prompt = _load_prompt(
        "user_prompt_rag.md",
        category=category,
        subcategory=subcategory if subcategory else "None",
        difficulty=difficulty,
        language=language,
        style=style,
        examples=examples_text,
    )

    # 모델 호출 (temperature 명시, JSON 모드)
    message = client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=RAG_TEMPERATURE,
    )

    # content만 추출
    response_text = message.choices[0].message.content

    # JSON 파싱 (실패 시 None — 호출 측에서 재시도)
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용: {response_text}")
        return None
