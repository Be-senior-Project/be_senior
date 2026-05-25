from .schemas import CategoryStat

_WEAK_THRESHOLD = 0.5  # 정답률 50% 미만이면 취약 카테고리


def find_weak_categories(stats: list[CategoryStat]) -> list[CategoryStat]:
    """정답률이 낮은 취약 카테고리를 반환. 없으면 최하위 1개."""
    weak = [s for s in stats if s.accuracy < _WEAK_THRESHOLD]
    if weak:
        return sorted(weak, key=lambda s: s.accuracy)
    # 모두 양호하면 가장 낮은 카테고리 1개 반환
    return [min(stats, key=lambda s: s.accuracy)] if stats else []


def compute_overall_accuracy(stats: list[CategoryStat]) -> float:
    total = sum(s.total_attempts for s in stats)
    correct = sum(s.correct_count for s in stats)
    return correct / total if total > 0 else 0.0


def infer_difficulty(overall_accuracy: float) -> str:
    """전체 정답률로 적정 난이도 추정."""
    if overall_accuracy < 0.3:
        return "입문"
    if overall_accuracy < 0.55:
        return "초급"
    if overall_accuracy < 0.75:
        return "중급"
    return "고급"
