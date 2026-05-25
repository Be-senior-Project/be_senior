import json
import os
import sys
from pathlib import Path

from openai import AsyncOpenAI

from .analyzer import find_weak_categories, compute_overall_accuracy, infer_difficulty
from .schemas import CategoryStat, PersonalizedResponse, RecommendedProblem

# topic_map은 프로젝트 루트에 위치
sys.path.insert(0, str(Path(__file__).parent.parent))
from topic_map import TOPIC_MAP

_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
_PROMPT_PATH = Path(__file__).parent / "prompts" / "personalized.md"


def _build_prompts(stats: list[CategoryStat]) -> tuple[str, str]:
    raw = _PROMPT_PATH.read_text(encoding="utf-8")
    system_part, user_part = raw.split("---USER---", 1)

    overall_acc = compute_overall_accuracy(stats)
    difficulty = infer_difficulty(overall_acc)
    weak = find_weak_categories(stats)

    stats_lines = "\n".join(
        f"- topic_id={s.topic_id} ({TOPIC_MAP.get(s.topic_id, '?')}): "
        f"정답률 {s.accuracy:.1%} ({s.correct_count}/{s.total_attempts})"
        for s in stats
    )
    weak_lines = ", ".join(
        f"{TOPIC_MAP.get(s.topic_id, '?')}(topic_id={s.topic_id})" for s in weak
    )

    user_prompt = user_part.strip().format(
        stats=stats_lines,
        weak_categories=weak_lines or "없음",
        overall_accuracy=f"{overall_acc:.1%}",
        suggested_difficulty=difficulty,
    )
    return system_part.strip(), user_prompt


async def recommend(user_id: int, stats: list[CategoryStat]) -> PersonalizedResponse:
    system_prompt, user_prompt = _build_prompts(stats)

    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    data = json.loads(response.choices[0].message.content)
    recommendations = [RecommendedProblem(**r) for r in data["recommendations"]]
    return PersonalizedResponse(recommendations=recommendations)
