from pydantic import BaseModel, Field, model_validator  # 요청/응답 구조 정의 및 입력값 검증
from typing import Optional # 타입 힌트
from dotenv import load_dotenv  # .env 파일에서 환경변수 로드

from app.core.enums import Category, AlgorithmSubcategory, Difficulty, Language, Style   # Enum 정의 (카테고리, 난이도, 언어, 스타일)
from app.core.config import MAX_COUNT

load_dotenv() # .env 파일에서 환경변수 로드

""" generate요청에 대한 응답 데이터 형식 지정 """
class GenerateResponse(BaseModel):
    requested: int
    saved: int
    failed: int
    problems: list[dict]

    
""" generate요청 데이터 형식 지정 및 요청 데이터 검증"""
class GenerateRequest(BaseModel):
    category: Category
    subcategory: Optional[AlgorithmSubcategory] = None
    difficulty: Difficulty
    language: Language
    style: Style
    count: int = Field(default=1, ge=1, le=MAX_COUNT)

    # 기초 카테고리로 설정된 경우 서브 카테고리 값을 넘겼는지 확인
    @model_validator(mode="after")
    def validate_subcategory(self):
        if self.category == Category.basic and self.subcategory is not None:
            raise ValueError("Basic/Introductory 카테고리는 서브 카테고리를 지정할 수 없습니다.")
        return self
