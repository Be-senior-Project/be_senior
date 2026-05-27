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


""" 임베딩할 항목 정의(제목, 설명, 개념 설명) """
def build_embed_text(problem: dict) -> str:
    prob = problem["Problem"]
    return "\n".join([
        prob.get("Title", ""),
        prob.get("Description", ""),
        problem.get("Concept Explanation", "")
    ])
