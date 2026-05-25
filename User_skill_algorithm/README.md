# User Skill Algorithm

하루코딩(HaruCoding) 플랫폼의 사용자 역량 기반 문제 추천 알고리즘 서비스.
신규 사용자 온보딩 추천과 기존 사용자 맞춤 추천 두 가지 플로우를 FastAPI로 제공한다.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.11+ |
| 프레임워크 | FastAPI + Uvicorn |
| AI | OpenAI GPT-4o-mini (JSON mode) |
| DB | PostgreSQL (asyncpg) |
| 외부 데이터 | Codeforces Problems API |

**추천 플로우 2종**

- **온보딩 추천** — 가입 직후 코딩 경험(NONE/SOME/LOTS)·코테 경험 여부를 입력받아 0~3점 점수로 초기 난이도를 결정하고 GPT가 추천 이유를 생성한다.
- **개인화 추천** — 카테고리별 풀이 이력(시도 횟수, 정답 수)을 분석해 취약 토픽과 적정 난이도를 추론하고 GPT가 문제별 추천 결과(`RecommendedProblem` 목록)를 생성한다.

---

## 2. 전체 폴더 구조

```
User_skill_algorithm/
│
├── db.py                          # asyncpg 커넥션 풀 싱글턴
├── topic_map.py                   # topic_id → 한글 이름 매핑 상수
├── requirements.txt
├── .env                           # 환경변수 (git 미포함)
│
├── data_pipeline/
│   ├── codeforces_collector.py    # Codeforces API → raw_problems.json
│   ├── difficulty_calibrator.py   # raw_problems.json → tag_stats.json
│   └── seed_data/
│       ├── raw_problems.json      # Codeforces 전체 문제 원본
│       └── tag_stats.json         # 태그별 난이도 분포 통계
│
├── onboarding_recommendation/
│   ├── schemas.py                 # Pydantic 모델 정의
│   ├── scorer.py                  # 코딩 레벨 → 0~3 점수 → 난이도 변환
│   ├── recommender.py             # 점수 기반 RecommendationFilter 생성
│   ├── api.py                     # FastAPI 라우터 (/recommend/onboarding)
│   └── prompts/
│       ├── onboarding.md          # GPT 프롬프트 (영문)
│       └── onboarding_kr.md       # GPT 프롬프트 (한국어)
│
└── personalized_recommendation/
    ├── schemas.py                 # Pydantic 모델 정의
    ├── analyzer.py                # 취약 카테고리 탐색·전체 정답률·난이도 추론
    ├── recommender.py             # 분석 결과 기반 GPT 호출 및 응답 파싱
    ├── api.py                     # FastAPI 라우터 (/recommend/personalized)
    └── prompts/
        ├── personalized.md        # GPT 프롬프트 (영문)
        └── personalized_kr.md     # GPT 프롬프트 (한국어)
```

---

## 3. 각 폴더 역할

| 폴더 | 역할 |
|------|------|
| `data_pipeline/` | 외부 데이터 수집·전처리 스크립트. 서비스 런타임에는 사용되지 않으며 씨드 데이터 생성 목적으로만 단독 실행한다. |
| `onboarding_recommendation/` | 신규 가입자 대상 추천. 규칙 기반 점수 계산으로 난이도를 결정하고 GPT로 추천 이유를 생성한다. |
| `personalized_recommendation/` | 기존 사용자 대상 추천. 카테고리별 정답률 통계를 분석한 뒤 GPT로 문제 추천 목록을 생성한다. |

---

## 4. 각 파일 기능

### 루트

| 파일 | 기능 |
|------|------|
| `db.py` | `get_pool()` / `close_pool()` — asyncpg 커넥션 풀을 전역 싱글턴으로 관리. `DATABASE_URL` 환경변수를 읽어 풀을 생성하며, 풀이 이미 존재하면 재사용한다. |
| `topic_map.py` | `TOPIC_MAP: dict[int, str]` — topic_id(1~4)를 한글 카테고리명으로 변환하는 상수 딕셔너리. `personalized_recommendation/recommender.py`에서 GPT 프롬프트 구성 시 사용한다. (`1=알고리즘, 2=자료구조, 3=언어/문법, 4=모의테스트`) |

### data_pipeline

| 파일 | 기능 |
|------|------|
| `codeforces_collector.py` | `fetch_problems()` — Codeforces `problemset.problems` API(`https://codeforces.com/api/problemset.problems`)를 호출해 전체 문제 목록을 반환. `save_problems()` — 결과를 `seed_data/raw_problems.json`에 저장. `__main__` 진입점으로 단독 실행 가능. |
| `difficulty_calibrator.py` | `map_difficulty(rating)` — Codeforces rating을 4단계 레이블로 변환 (`800~1200=입문 / 1300~1600=초급 / 1700~2100=중급 / 2200+=고급`). `calibrate()` — `raw_problems.json`을 읽어 태그별 난이도 분포를 집계하고 `seed_data/tag_stats.json`에 저장. `__main__` 진입점으로 단독 실행 가능. |

### onboarding_recommendation

| 파일 | 기능 |
|------|------|
| `schemas.py` | `CodingLevel` enum(NONE/SOME/LOTS), `UserProfile(coding_level, cote_prepared)`, `RecommendationFilter(difficulty, topic_ids)`, `OnboardingRequest(user)`, `OnboardingResponse(filter, reason)` Pydantic 모델 정의. |
| `scorer.py` | `compute_score(profile)` — `CodingLevel`을 정수(NONE=0, SOME=1, LOTS=2)로 변환하고 `cote_prepared=True`이면 +1, 최대 3으로 클램핑. `score_to_difficulty(score)` — 0→입문, 1→초급, 2→중급, 3→고급으로 변환. |
| `recommender.py` | `recommend(profile)` — `scorer`를 호출해 난이도를 결정하고 `topic_ids=[1, 2, 3, 4]`(전체 토픽)를 포함한 `RecommendationFilter`를 반환. |
| `api.py` | `POST /recommend/onboarding` — `recommend()`로 필터를 결정. `_load_prompts(difficulty, coding_level, cote_prepared)`로 `onboarding.md` USER 섹션을 포맷팅. GPT-4o-mini를 호출해 `data["reason"]`을 추출하고 `OnboardingResponse`로 반환. |
| `prompts/onboarding.md` | GPT 시스템·유저 프롬프트(영문). `---USER---` 구분자로 분리. USER 섹션은 `{coding_level_label}`, `{coding_level}`, `{cote_prepared_label}`, `{preferred_language}`, `{score}` 플레이스홀더를 포함하며, GPT 응답 형식은 `{ difficulty, topic_ids, language, reason, focus_point }`. |
| `prompts/onboarding_kr.md` | `onboarding.md`와 동일 구조의 한국어 프롬프트. |

> **주의**: `api.py`의 `_load_prompts()`는 `{difficulty}`, `{coding_level}`, `{cote_prepared}` 세 변수를 전달하지만, `onboarding.md` USER 섹션은 `{coding_level_label}`, `{cote_prepared_label}`, `{preferred_language}`, `{score}` 등 다른 이름의 변수를 사용한다. 이로 인해 런타임에서 `str.format()` 호출이 실패할 수 있다.

### personalized_recommendation

| 파일 | 기능 |
|------|------|
| `schemas.py` | `CategoryStat(topic_id, total_attempts, correct_count)` — `accuracy` 계산 필드(`@computed_field`) 포함. `PersonalizedRequest(user_id, category_stats)`, `RecommendedProblem(topic_id, difficulty, reason)`, `PersonalizedResponse(recommendations)` 모델 정의. |
| `analyzer.py` | `find_weak_categories(stats)` — 정답률 50% 미만 카테고리 반환. 모두 양호하면 정답률 최하위 1개 반환. `compute_overall_accuracy(stats)` — 전체 시도 수 대비 전체 정답 수로 정확도 계산. `infer_difficulty(accuracy)` — `<0.3=입문 / 0.3~0.55=초급 / 0.55~0.75=중급 / ≥0.75=고급`. |
| `recommender.py` | `_build_prompts(stats)` — `analyzer` 결과와 `TOPIC_MAP`으로 `personalized.md` USER 섹션을 `{stats}`, `{weak_categories}`, `{overall_accuracy}`, `{suggested_difficulty}` 네 변수로 포맷팅. `recommend(user_id, stats)` — GPT-4o-mini를 호출해 `data["recommendations"]` 목록을 파싱하고 `PersonalizedResponse`로 반환. |
| `api.py` | `POST /recommend/personalized` — `recommend()`를 호출하는 얇은 라우터. |
| `prompts/personalized.md` | GPT 시스템·유저 프롬프트(영문). USER 섹션은 `{level}`, `{coding_level_label}`, `{cote_prepared_label}`, `{preferred_language}`, `{total_solved}`, `{correct_rate}`, `{avg_time_sec}`, `{category_stats}`, `{weak_topic_ids}`, `{strong_topic_ids}` 플레이스홀더를 포함하며, GPT 응답 형식은 `{ difficulty, topic_ids, type, style, language, reason, focus_point }`. |
| `prompts/personalized_kr.md` | `personalized.md`와 동일 구조의 한국어 프롬프트. |

> **주의**: `recommender.py`의 `_build_prompts()`는 `{stats}`, `{weak_categories}`, `{overall_accuracy}`, `{suggested_difficulty}` 네 변수를 전달하지만, `personalized.md` USER 섹션은 `{level}`, `{category_stats}`, `{weak_topic_ids}` 등 다른 이름의 변수를 사용한다. 프롬프트와 코드 간 변수명 불일치가 있다.

---

## 5. 데이터 흐름

### 온보딩 추천

```
클라이언트 POST /recommend/onboarding
    │
    └─ OnboardingRequest { user: UserProfile(coding_level, cote_prepared) }
    │
    ▼
scorer.compute_score(profile)
    NONE=0 / SOME=1 / LOTS=2, cote_prepared=True → +1, max 3
    │
scorer.score_to_difficulty(score)
    0→입문 / 1→초급 / 2→중급 / 3→고급
    │
recommender.recommend(profile)
    → RecommendationFilter(difficulty, topic_ids=[1,2,3,4])
    │
api._load_prompts(difficulty, coding_level, cote_prepared)
    onboarding.md 템플릿 포맷팅
    │
OpenAI GPT-4o-mini (json_object mode)
    → { "reason": "..." }
    │
    ▼
OnboardingResponse(filter=RecommendationFilter, reason=str)
```

### 개인화 추천

```
클라이언트 POST /recommend/personalized
    │
    └─ PersonalizedRequest { user_id, category_stats: [CategoryStat, ...] }
    │
    ▼
analyzer.compute_overall_accuracy(stats)   → float (전체 정답률)
analyzer.infer_difficulty(accuracy)        → 난이도 문자열
analyzer.find_weak_categories(stats)       → 정답률 <50% 카테고리 목록
    │
recommender._build_prompts(stats)
    TOPIC_MAP으로 topic_id → 한글 이름 변환
    stats_lines / weak_lines 문자열 조합
    personalized.md 템플릿 포맷팅
    │
OpenAI GPT-4o-mini (json_object mode)
    → { "recommendations": [{ topic_id, difficulty, reason }, ...] }
    │
    ▼
PersonalizedResponse(recommendations=[RecommendedProblem, ...])
```

### 데이터 파이프라인 (오프라인)

```
Codeforces API (https://codeforces.com/api/problemset.problems)
    │
codeforces_collector.py  →  seed_data/raw_problems.json
    │
difficulty_calibrator.py →  seed_data/tag_stats.json
    (rating → 4단계 레이블 변환, 태그별 난이도 분포 집계)
```

---

## 6. 외부 의존성

| 시스템 | 용도 | 비고 |
|--------|------|------|
| **Codeforces API** | `https://codeforces.com/api/problemset.problems` — 문제 원본 수집 | 오프라인 파이프라인(`codeforces_collector.py`)에서만 사용. 서비스 런타임에는 미사용. |
| **OpenAI API** | GPT-4o-mini — 추천 이유(`reason`) 및 문제 추천 목록 JSON 생성 | `OPENAI_API_KEY` 환경변수 필요. `response_format={"type": "json_object"}` 모드 사용. `AsyncOpenAI` 클라이언트 사용(비동기). |
| **PostgreSQL** | asyncpg 커넥션 풀(`db.py`) 준비 | `DATABASE_URL` 환경변수로 연결. 현재 API 라우터에서 직접 쿼리는 미구현이며 `db.py`가 풀을 사전 준비한다. |

---

## 7. 환경변수 목록

`.env` 파일을 프로젝트 루트에 생성한다. `python-dotenv`가 자동으로 로드한다.

| 변수명 | 필수 | 설명                                                                                                          |
|--------|------|-------------------------------------------------------------------------------------------------------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 인증 키. `onboarding_recommendation/api.py`와 `personalized_recommendation/recommender.py`에서 직접 읽는다. |
| `DATABASE_URL` | ✅ | asyncpg 연결 문자열. 예: `postgresql://postgres:postgres@db:5432/problem`                                         |
| `DB_HOST` | (참고) | Docker Compose에서 PostgreSQL 컨테이너 호스트명                                                                       |
| `DB_PORT` | (참고) | PostgreSQL 포트 (기본 5432)                                                                                     |
| `DB_NAME` | (참고) | DB 이름                                                                                                       |
| `DB_USER` | (참고) | DB 사용자                                                                                                      |
| `DB_PASSWORD` | (참고) | DB 비밀번호                                                                                                     |
| `PGADMIN_EMAIL` | (선택) | pgAdmin 로그인 이메일                                                                                             |
| `PGADMIN_PASSWORD` | (선택) | pgAdmin 비밀번호                                                                                                |

> `db.py`는 `DATABASE_URL` 하나만 사용한다. 나머지 `DB_*` 변수들은 Docker Compose에서 PostgreSQL 컨테이너를 구성할 때 사용한다.

---

## 8. 실행 방법

### 의존성 설치

```bash
pip install -r requirements.txt
```

주요 패키지: `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0`, `asyncpg>=0.30.0`, `openai>=1.0.0`, `pydantic>=2.0.0`, `httpx>=0.27.0`, `python-dotenv>=1.0.0`

### 환경변수 설정

```bash
# .env 파일 생성
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/problems_db
```

### 데이터 파이프라인 실행 (씨드 데이터 갱신 시)

```bash
# Codeforces에서 문제 수집 → seed_data/raw_problems.json
python -m data_pipeline.codeforces_collector

# 태그별 난이도 통계 생성 → seed_data/tag_stats.json
python -m data_pipeline.difficulty_calibrator
```

### API 서버 실행

`main.py`가 없으므로 라우터를 포함한 진입점을 직접 작성해야 한다.

```python
# main.py 예시
from fastapi import FastAPI
from onboarding_recommendation.api import router as onboarding_router
from personalized_recommendation.api import router as personalized_router

app = FastAPI()
app.include_router(onboarding_router)
app.include_router(personalized_router)
```

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API 엔드포인트 요약

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/recommend/onboarding` | 신규 사용자 온보딩 추천 |
| `POST` | `/recommend/personalized` | 기존 사용자 개인화 추천 |

**온보딩 요청 예시**

```json
POST /recommend/onboarding
{
  "user": {
    "coding_level": "SOME",
    "cote_prepared": false
  }
}
```

응답:
```json
{
  "filter": {
    "difficulty": "초급",
    "topic_ids": [1, 2, 3, 4]
  },
  "reason": "GPT가 생성한 추천 이유 문자열"
}
```

**개인화 요청 예시**

```json
POST /recommend/personalized
{
  "user_id": 42,
  "category_stats": [
    { "topic_id": 1, "total_attempts": 10, "correct_count": 3 },
    { "topic_id": 2, "total_attempts": 8,  "correct_count": 6 }
  ]
}
```

응답:
```json
{
  "recommendations": [
    { "topic_id": 1, "difficulty": "초급", "reason": "GPT가 생성한 이유" }
  ]
}
```
