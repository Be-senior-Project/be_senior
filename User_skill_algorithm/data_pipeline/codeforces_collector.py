import httpx
import json
from pathlib import Path

CF_API_URL = "https://codeforces.com/api/problemset.problems"
OUTPUT_PATH = Path(__file__).parent / "seed_data" / "raw_problems.json"


def fetch_problems() -> list[dict]:
    response = httpx.get(CF_API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data["status"] != "OK":
        raise RuntimeError(f"Codeforces API error: {data['comment']}")
    return data["result"]["problems"]


def save_problems(problems: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(problems)} problems → {OUTPUT_PATH}")


if __name__ == "__main__":
    problems = fetch_problems()
    save_problems(problems)
