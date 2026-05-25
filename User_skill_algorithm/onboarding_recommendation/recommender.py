from .scorer import compute_score, score_to_difficulty
from .schemas import UserProfile, RecommendationFilter

_ALL_TOPIC_IDS = [1, 2, 3, 4]


def recommend(profile: UserProfile) -> RecommendationFilter:
    score = compute_score(profile)
    difficulty = score_to_difficulty(score)
    return RecommendationFilter(difficulty=difficulty, topic_ids=_ALL_TOPIC_IDS)
