from .schemas import CodingLevel, UserProfile

_LEVEL_SCORE: dict[CodingLevel, int] = {
    CodingLevel.NONE: 0,
    CodingLevel.SOME: 1,
    CodingLevel.LOTS: 2,
}

_DIFFICULTY_MAP: dict[int, str] = {
    0: "입문",
    1: "초급",
    2: "중급",
    3: "고급",
}


def compute_score(profile: UserProfile) -> int:
    score = _LEVEL_SCORE[profile.coding_level]
    if profile.cote_prepared:
        score += 1
    return min(score, 3)


def score_to_difficulty(score: int) -> str:
    return _DIFFICULTY_MAP[score]
