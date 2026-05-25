import json
import os
from pathlib import Path

from fastapi import APIRouter
from openai import AsyncOpenAI

from .recommender import recommend
from .schemas import OnboardingRequest, OnboardingResponse

router = APIRouter()
_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
_PROMPT_PATH = Path(__file__).parent / "prompts" / "onboarding.md"


def _load_prompts(difficulty: str, coding_level: str, cote_prepared: bool) -> tuple[str, str]:
    raw = _PROMPT_PATH.read_text(encoding="utf-8")
    system_part, user_part = raw.split("---USER---", 1)
    user_prompt = user_part.strip().format(
        difficulty=difficulty,
        coding_level=coding_level,
        cote_prepared="예" if cote_prepared else "아니오",
    )
    return system_part.strip(), user_prompt


@router.post("/recommend/onboarding", response_model=OnboardingResponse)
async def onboarding_recommend(body: OnboardingRequest) -> OnboardingResponse:
    rec_filter = recommend(body.user)

    system_prompt, user_prompt = _load_prompts(
        difficulty=rec_filter.difficulty,
        coding_level=body.user.coding_level.value,
        cote_prepared=body.user.cote_prepared,
    )

    gpt_response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    data = json.loads(gpt_response.choices[0].message.content)
    return OnboardingResponse(filter=rec_filter, reason=data["reason"])
