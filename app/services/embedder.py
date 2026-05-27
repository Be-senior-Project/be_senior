from openai import OpenAI
from dotenv import load_dotenv

from app.core.config import EMBEDDING_MODEL

load_dotenv()



""" 임베딩 """
def get_embedding(text: str) -> list[float]:
    client = OpenAI()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


""" 임베딩할 항목 정의

RAG retrieve 정확도를 높이기 위해 자연어 신호 위주로 구성한다.
- Type: 문제 유형(Implementation/Debugging/Fill-in-the-blank). 같은 유형끼리 가까워지도록 prefix처럼 한 줄.
- Title / Description: 문제의 표면적 키워드와 본문.
- Concept Explanation: 핵심 알고리즘/개념 설명. 같은 주제 매칭에 가장 강한 신호.
- Constraints: 입력 규모/난이도 힌트.
- Explanation: 풀이 전략과 시간 복잡도. 같은 접근법 매칭에 유효.

category/subcategory/language는 SQL WHERE로 필터링하므로 임베딩 텍스트에서 제외(노이즈 방지).
"""
def build_embed_text(problem: dict) -> str:
    prob = problem["Problem"]
    constraints = prob.get("Constraints", []) or []
    explanation = prob.get("Explanation", "")

    parts = [
        f"[Type: {prob.get('Type', '')}]",
        prob.get("Title", ""),
        prob.get("Description", ""),
        problem.get("Concept Explanation", ""),
    ]
    if constraints:
        parts.append("Constraints:\n" + "\n".join(f"- {c}" for c in constraints))
    if explanation:
        parts.append("Explanation:\n" + explanation)

    return "\n".join(parts)
