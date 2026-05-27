import json
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from app.core.config import PROMPTS_DIR, GENERATION_MODEL

load_dotenv()

def _get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일 또는 환경변수를 확인하세요.")
    return OpenAI()

""" 프롬프트 md 파일 getter 함수 """
def _load_prompt(filename: str, **kwargs) -> str:
    prompt = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    # **kwargs에 값이 있을 경우 해당 값을 prompt 포멧에 맞춰서 반환, 없을 경우는 prompt만 반환
    return prompt.format(**kwargs) if kwargs else prompt


""" 문제 생성 """
def generate_problem(
    category: str,
    difficulty: str,
    language: str,
    style: str,
    subcategory: Optional[str] = None
) -> Optional[dict]:
    
    # OpenAPI 키 설정
    client = _get_client()

    # system, user 프롬프트 읽어오기
    system_prompt = _load_prompt("system_prompt.md")
    user_prompt = _load_prompt(
        "user_prompt.md",
        category=category,
        subcategory=subcategory if subcategory else "None",
        difficulty=difficulty,
        language=language,
        style=style
    )

    # 모델이 문제 생성 요청
    message = client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
    )

    # 모델 응답 중 content만 선택
    response_text = message.choices[0].message.content

    # json타입인 content를 로드해서 성공하면 반환, 실패 시 json 형식으로 응답되지 않은 것으로 간주하여 None 반환
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용: {response_text}")
        return None