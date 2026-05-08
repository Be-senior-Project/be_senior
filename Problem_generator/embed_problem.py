import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding(text: str) -> list[float]:
    client = OpenAI()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def build_embed_text(problem: dict) -> str:
    """임베딩할 텍스트 구성: 제목 + 설명 + 개념 설명"""
    prob = problem["Problem"]
    return "\n".join([
        prob.get("Title", ""),
        prob.get("Description", ""),
        problem.get("Concept Explanation", "")
    ])
