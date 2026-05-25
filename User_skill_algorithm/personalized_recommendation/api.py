from fastapi import APIRouter

from .recommender import recommend
from .schemas import PersonalizedRequest, PersonalizedResponse

router = APIRouter()


@router.post("/recommend/personalized", response_model=PersonalizedResponse)
async def personalized_recommend(body: PersonalizedRequest) -> PersonalizedResponse:
    return await recommend(body.user_id, body.category_stats)
