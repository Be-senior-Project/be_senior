from pydantic import BaseModel, computed_field


class CategoryStat(BaseModel):
    topic_id: int
    total_attempts: int
    correct_count: int

    @computed_field
    @property
    def accuracy(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.correct_count / self.total_attempts


class PersonalizedRequest(BaseModel):
    user_id: int
    category_stats: list[CategoryStat]


class RecommendedProblem(BaseModel):
    topic_id: int
    difficulty: str   # 입문 / 초급 / 중급 / 고급
    reason: str


class PersonalizedResponse(BaseModel):
    recommendations: list[RecommendedProblem]
