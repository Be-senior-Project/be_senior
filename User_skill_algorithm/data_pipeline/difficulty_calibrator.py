import json
from collections import defaultdict
from pathlib import Path

RAW_PATH = Path(__file__).parent / "seed_data" / "raw_problems.json"
OUTPUT_PATH = Path(__file__).parent / "seed_data" / "tag_stats.json"

# (min_rating, max_rating) → difficulty label
RATING_BANDS: list[tuple[int, int, str]] = [
    (800,  1200, "입문"),
    (1300, 1600, "초급"),
    (1700, 2100, "중급"),
    (2200, 9999, "고급"),
]


def map_difficulty(rating: int) -> str | None:
    for lo, hi, level in RATING_BANDS:
        if lo <= rating <= hi:
            return level
    return None


def calibrate() -> None:
    with open(RAW_PATH, encoding="utf-8") as f:
        problems: list[dict] = json.load(f)

    tag_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for p in problems:
        rating = p.get("rating")
        tags: list[str] = p.get("tags", [])
        if not rating or not tags:
            continue
        diff = map_difficulty(rating)
        if diff is None:
            continue
        for tag in tags:
            tag_stats[tag][diff] += 1

    result = {tag: dict(counts) for tag, counts in sorted(tag_stats.items())}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved tag stats ({len(result)} tags) → {OUTPUT_PATH}")


if __name__ == "__main__":
    calibrate()
