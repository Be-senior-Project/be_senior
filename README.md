# Problem Generator (RAG 버전)

GPT + RAG(Retrieval-Augmented Generation)로 프로그래머스 스타일의 코딩 테스트 문제를 자동 생성하고, PostgreSQL(pgvector)에 저장하는 API 서버입니다.

> 이 브랜치(`generator_rag`)는 prompt-only 버전(`generator_prompt`)의 RAG 확장판입니다.
> 시드 문제 풀에서 유사한 예시를 가져와 프롬프트 컨텍스트로 끼워 넣어 할루시네이션을 줄입니다.

## 기술 스택

- **FastAPI** - API 서버
- **OpenAI GPT-5.4-mini** - 문제 생성 (RAG 모드는 `temperature=0.4`)
- **OpenAI text-embedding-3-small** - 시드/쿼리 임베딩
- **PostgreSQL + pgvector** - 문제 저장 + HNSW 코사인 ANN 인덱스로 RAG 검색
- **Docker** - DB, pgAdmin, API 서버 실행 (컴파일러 포함)

## 프로젝트 구조

```
be_senior/
├── app/
│   ├── main.py                       # FastAPI 앱 진입점
│   ├── api/
│   │   └── generate.py               # /generate 라우터 (시드 존재 여부로 SEED/RAG 분기)
│   ├── schemas/
│   │   └── request.py                # 요청/응답 Pydantic 모델
│   ├── services/
│   │   ├── generator.py                  # prompt-only 문제 생성 (시드 채움용)
│   │   ├── rag_generator.py              # RAG 문제 생성 (examples 컨텍스트 + temp=0.4)
│   │   ├── retriever.py                  # pgvector 코사인 top-k 검색
│   │   ├── verifier.py                   # 생성된 문제 검증 진입점
│   │   ├── embedder.py                   # 임베딩 생성 (Title+Description+Concept+Constraints+Explanation+Type)
│   │   ├── problem_service_pipeline.py   # 시드 채움 파이프라인 (prompt-only)
│   │   ├── rag_problem_pipeline.py       # RAG 파이프라인 (retrieve→generate→verify→save)
│   │   └── runners/                      # 언어별 코드 실행기
│   │       ├── base.py
│   │       ├── python_runner.py
│   │       ├── java_runner.py
│   │       └── cpp_runner.py
│   ├── repositories/
│   │   └── problem_repo.py           # PostgreSQL 저장 + 시드 카운트 + HNSW 인덱스 init
│   └── core/
│       ├── config.py                 # 환경변수/상수 (RAG_TOP_K, RAG_TEMPERATURE 포함)
│       └── enums.py                  # 입력값 Enum 정의
├── prompts/
│   ├── system_prompt.md              # 시스템 프롬프트 (영문, 공통)
│   ├── system_prompt_kr.md           # 시스템 프롬프트 (국문, 참조용)
│   ├── user_prompt.md                # 유저 프롬프트 — 시드 채움용 (영문)
│   ├── user_prompt_kr.md             # 유저 프롬프트 — 시드 채움용 (국문)
│   ├── user_prompt_rag.md            # 유저 프롬프트 — RAG용 ({examples} 슬롯, 영문)
│   └── user_prompt_rag_kr.md         # 유저 프롬프트 — RAG용 (국문)
├── Dockerfile                        # API 서버 Docker 이미지 (JDK, g++ 포함)
├── docker-compose.yml                # DB, pgAdmin, API 컨테이너 설정
├── requirements.txt                  # Python 의존성 (pgvector 포함)
├── .env                              # 환경변수 (git 제외)
└── .env.example                      # 환경변수 예시 (git 포함)
```

## 시작하기

### 1. 저장소 클론

```
git clone https://github.com/Be-senior-Project/be_senior.git
cd be_senior
```

### 2. 환경변수 설정

`.env.example`을 복사해서 `.env` 파일을 만들고 값을 채워주세요.

```
cp .env.example .env
```

`.env` 파일:

```
OPENAI_API_KEY=카카오톡을 통해 공유된 API 키 넣기("" 없이)
DB_HOST=db
DB_PORT=5432
DB_NAME=problems_db
DB_USER=postgres
DB_PASSWORD=postgres
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
MAX_COUNT=50
MAX_CONCURRENT=10
RAG_TOP_K=3
RAG_TEMPERATURE=0.4
```

> ※ Docker Compose로 실행할 때 API 컨테이너는 같은 네트워크의 `db` 호스트명을 사용하므로 `DB_HOST=db` 로 설정합니다. 로컬에서 uvicorn으로 직접 띄울 때는 `DB_HOST=localhost` 로 변경하세요.

### 3. Docker로 전체 실행

Docker Desktop이 설치되어 있어야 합니다.

```
docker-compose up --build
```

| 서비스 | 주소 |
| --- | --- |
| API 서버 | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| pgAdmin | http://localhost:5050 |

**pgAdmin 최초 접속 시 서버 등록:**

```
General 탭:
  Name: problems_db (아무거나)

Connection 탭:
  Host: db
  Port: 5432
  Database: problems_db
  Username: postgres
  Password: postgres
```


## API 사용법

### POST /generate

문제를 생성하고 PostgreSQL에 저장합니다. 검증에 실패한 문제는 자동으로 제외됩니다. (최대 3회 재시도)

**요청 파라미터:**

| 파라미터 | 필수 | 타입 | 설명 |
| --- | --- | --- | --- |
| category | ✅ | string | 대단원 |
| subcategory | ❌ | string | 중단원 (Algorithm/Data Structure 카테고리에서만 사용) |
| difficulty | ✅ | string | 난이도 |
| language | ✅ | string | 언어 |
| style | ✅ | string | 문제 스타일 |
| count | ❌ | integer | 생성 개수 (기본값: 1, 최대: `MAX_COUNT` 환경변수, 기본 50) |

**category / subcategory 옵션:**

| category | subcategory |
| --- | --- |
| `Basic/Introductory` | 없음 |
| `Algorithm/Data Structure` | `Hash`, `Stack/Queue`, `Heap`, `Sort`, `Brute Force`, `Greedy`, `Dynamic Programming`, `DFS/BFS`, `Binary Search`, `Graph` |

**difficulty 옵션:** `0`, `1`, `2`

**language 옵션:** `Python`, `Java`, `C++`

**style 옵션:**

| style | 설명 |
| --- | --- |
| `General` | 간결하고 straightforward한 스타일 |
| `Kakao` | 짧은 스토리텔링이 포함된 카카오 스타일 |
| `Contest` | 간결하지만 고난이도 제약조건의 대회 스타일 |

**요청 예시:**

```
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Algorithm/Data Structure",
    "subcategory": "DFS/BFS",
    "difficulty": "2",
    "language": "Python",
    "style": "General",
    "count": 5
  }'
```

**응답 예시:**

```
{
  "requested": 5,
  "saved": 4,
  "failed": 1,
  "problems": [...]
}
```

## 생성되는 문제 JSON 구조

```
{
  "Concept Explanation": "...",
  "Problem": {
    "Type": "Implementation | Debugging | Fill-in-the-blank",
    "Title": "...",
    "Description": "...",
    "Constraints": ["..."],
    "Signature": "def solution(n, arr):",
    "IO Example": {
      "input": "n = 5\narr = [1, 2, 3, 4, 5]",
      "output": "15"
    },
    "Code Skeleton": "...",
    "Answer": "...",
    "Explanation": "..."
  }
}
```

- `Signature`: 요청 언어 문법 그대로의 함수 시그니처
- `IO Example.input`: 해당 언어의 변수 선언문 (변수명은 Signature 파라미터와 일치)
- `Code Skeleton` / `Answer`: 문제 Type에 따라 형태가 다름
  - `Implementation`: Code Skeleton = `null`, Answer = 완성 함수 코드
  - `Debugging`: Code Skeleton = 버그 코드, Answer = 수정된 코드
  - `Fill-in-the-blank`: Code Skeleton = `{{BLANK_1}}` 플레이스홀더가 있는 코드, Answer = 빈칸 정답 문자열 배열

## 문제 생성 흐름

`/generate` 호출 시 요청 `(category, subcategory, language)` 조합의 시드 문제가 DB에 있는지 먼저 확인하여 두 가지 모드로 분기됩니다.

### 모드 1: SEED — 시드 채움 (prompt-only)

해당 조합의 row가 **0건**이면 자동으로 진입. 기존 prompt-only 방식으로 문제를 생성해 시드 풀을 채웁니다.

```
POST /generate
    ↓
count_seeds() == 0     → SEED 모드 진입
    ↓
generate_problem()     GPT로 문제 생성 (프롬프트만, JSON 모드)
    ↓
verify_problem()       언어별 runner에서 코드 컴파일/실행 검증
    ↓
get_embedding()        build_embed_text(자연어 6필드) → 임베딩
    ↓
save_problem()         PostgreSQL(pgvector) 저장
    ↓
JSON 응답 반환
```

### 모드 2: RAG — 검색 증강 생성

해당 조합의 row가 **1건 이상**이면 자동으로 진입.

```
POST /generate
    ↓
count_seeds() > 0      → RAG 모드 진입
    ↓
retrieve_similar_problems()
    ├─ 요청 → 쿼리 텍스트 합성 → get_embedding()
    └─ (category, subcategory, language) 필터 + ORDER BY embedding <=> $q (HNSW 코사인)
    → top-k 시드 dict 리스트
    ↓
generate_problem_with_rag()
    examples 컨텍스트 + user_prompt_rag.md + temperature=0.4 → GPT (JSON 모드)
    ↓
verify_problem()       (동일)
    ↓
get_embedding() + save_problem()   생성본도 problems 테이블에 저장
    ↓
JSON 응답 반환
```

### 공통 동작

- 검증 실패 시 **MAX_RETRIES(기본 3)** 회 재시도. 모두 실패한 문제는 결과에서 제외, 콘솔에 사유 출력(컴파일 에러, 런타임 에러, 시간 초과, 출력 불일치 등).
- RAG 모드에서 retrieve는 첫 1회만 수행하고 재시도 루프 내내 같은 examples 재사용 (임베딩 비용 절약).
- 여러 개 동시 생성 시 `MAX_CONCURRENT`(기본 10)만큼 병렬 처리.

## RAG 설계 메모

- **임베딩 항목**: `Type + Title + Description + Concept Explanation + Constraints + Explanation`. category/subcategory/language는 SQL 필터에서 잡으므로 임베딩 텍스트에서 제외(노이즈 방지).
- **인덱스**: HNSW + `vector_cosine_ops`로 ANN 검색. 시드가 늘어나도 retrieve 비용 안정.
- **시드와 RAG 생성본 구분 없음**: 두 경로 모두 `problems` 테이블에 같은 형태로 저장. RAG 결과가 다음 retrieve의 시드 풀에 자연스럽게 합류.
- **temperature 0.4**: 일관성과 다양성의 절충점. `RAG_TEMPERATURE` 환경변수로 조절.