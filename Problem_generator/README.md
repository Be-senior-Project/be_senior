# Problem Generator

GPT를 활용하여 프로그래머스 스타일의 코딩 테스트 문제를 자동 생성하고, PostgreSQL(pgvector)에 저장하는 API 서버입니다.

## 기술 스택

- **FastAPI** - API 서버
- **OpenAI GPT-5.4-mini** - 문제 생성
- **OpenAI text-embedding-3-small** - 임베딩
- **PostgreSQL + pgvector** - 문제 및 벡터 저장
- **Docker** - DB 및 pgAdmin 실행

## 프로젝트 구조

```
Problem_generator/
├── main.py               # FastAPI 앱 및 전체 흐름
├── generate_problem.py   # GPT 문제 생성
├── verify_problem.py     # 생성된 문제 검증 (subprocess)
├── embed_problem.py      # 임베딩 생성
├── db.py                 # PostgreSQL 저장
├── enums.py              # 입력값 Enum 정의
├── Dockerfile            # API 서버 Docker 이미지
├── docker-compose.yml    # DB, pgAdmin 컨테이너 설정
├── requirements.txt      # Python 의존성
├── prompts/
│   ├── system_prompt.md  # GPT 시스템 프롬프트
│   └── user_prompt.md    # GPT 유저 프롬프트
├── .env                  # 환경변수 (git 제외)
└── .env.example          # 환경변수 예시 (git 포함)
```

## 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/Be-senior-Project/be_senior.git
cd be_senior/Problem_generator
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example`을 복사해서 `.env` 파일을 만들고 값을 채워주세요.

```bash
cp .env.example .env
```

`.env` 파일:

```
OPENAI_API_KEY=카카오톡을 통해 공유된 API 키 넣기("" 없이)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=problems_db
DB_USER=postgres
DB_PASSWORD=postgres
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
```

### 4. Docker로 DB 및 pgAdmin 띄우기

Docker Desktop이 설치되어 있어야 합니다.

```bash
# DB와 pgAdmin 실행
docker-compose up db pgadmin
```

| 서비스 | 주소 |
|--------|------|
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

### 5. FastAPI 서버 실행

```bash
uvicorn main:app --reload
```

| 서비스 | 주소 |
|--------|------|
| API 서버 | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

## API 사용법

### POST /generate

문제를 생성하고 PostgreSQL에 저장합니다. 검증에 실패한 문제는 자동으로 제외됩니다. (최대 3회 재시도)

**요청 파라미터:**

| 파라미터 | 필수 | 타입 | 설명 |
|----------|------|------|------|
| category | ✅ | string | 대단원 |
| subcategory | ❌ | string | 중단원 (category에 따라 다름) |
| difficulty | ✅ | string | 난이도 |
| language | ✅ | string | 언어 |
| style | ✅ | string | 문제 스타일 |
| count | ❌ | integer | 생성 개수 (기본값: 1, 최대: 10) |

**category / subcategory 옵션:**

| category | subcategory |
|----------|-------------|
| `Basic/Introductory` | 없음 |
| `Algorithm/Data Structure` | `Hash`, `Stack/Queue`, `Heap`, `Sort`, `Brute Force`, `Greedy`, `Dynamic Programming`, `DFS/BFS`, `Binary Search`, `Graph` |
| `SQL` | `SELECT`, `SUM/MAX/MIN`, `GROUP BY`, `IS NULL`, `JOIN`, `String/Date` |

**difficulty 옵션:** `0`, `1`, `2`

**language 옵션:** `Python`, `Java`, `C++`, `SQL`

**style 옵션:**

| style | 설명 |
|-------|------|
| `General` | 간결하고 straightforward한 스타일 |
| `Kakao` | 스토리텔링이 포함된 카카오 스타일 |
| `Contest` | 간결하지만 고난이도 제약조건의 대회 스타일 |

**요청 예시:**

```bash
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

```json
{
  "requested": 5,
  "saved": 4,
  "failed": 1,
  "problems": [...]
}
```

## 문제 생성 흐름

```
POST /generate
    ↓
generate_problem()     GPT로 문제 생성
    ↓
verify_problem()       정답 코드 실행 검증 (subprocess)
    ↓
get_embedding()        문제 텍스트 임베딩
    ↓
save_problem()         PostgreSQL 저장
    ↓
JSON 응답 반환
```

검증 실패 시 최대 3회 재시도하며, 3회 모두 실패한 문제는 결과에서 제외됩니다.
