import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).parent / "prompts"
GENERATION_MODEL = "gpt-5.4-mini"


def _get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일 또는 환경변수를 확인하세요.")
    return OpenAI()


def _load_prompt(filename: str, **kwargs) -> str:
    prompt = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return prompt.format(**kwargs) if kwargs else prompt


def generate_problem(category: str, difficulty: str, language: str, style: str) -> dict:
    client = _get_client()

    system_prompt = _load_prompt("system_prompt.md")
    user_prompt = _load_prompt(
        "user_prompt.md",
        category=category,
        difficulty=difficulty,
        language=language,
        style=style
    )

    message = client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    response_text = message.choices[0].message.content

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용: {response_text}")
        return None