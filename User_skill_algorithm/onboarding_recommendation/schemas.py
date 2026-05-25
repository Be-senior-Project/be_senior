from enum import Enum
from pydantic import BaseModel


class CodingLevel(str, Enum):
    NONE = "NONE"
    SOME = "SOME"
    LOTS = "LOTS"


class UserProfile(BaseModel):
    coding_level: CodingLevel
    cote_prepared: bool


class RecommendationFilter(BaseModel):
    difficulty: str          # 입문 / 초급 / 중급 / 고급
    topic_ids: list[int]     # problems 테이블 조회 조건


class OnboardingRequest(BaseModel):
    user: UserProfile


class OnboardingResponse(BaseModel):
    filter: RecommendationFilter
    reason: str              # GPT가 생성한 추천 이유
