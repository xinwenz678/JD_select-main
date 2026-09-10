from fastapi import APIRouter, Request
from app.schemas.suggestion import StarSuggestionRequest, StarSuggestionResponse
from app.services.star_suggestions import build_star_suggestion

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

@router.post("/star", response_model=StarSuggestionResponse)
def create_star_suggestion(payload: StarSuggestionRequest, request: Request):
    return build_star_suggestion(payload.experience, payload.jd_text, request.app.state.settings)
