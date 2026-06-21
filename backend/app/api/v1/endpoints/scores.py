from fastapi import APIRouter, Query

from app.data.repository import get_repository
from app.schemas.score import ScoreMapItem, ScoreMapResponse, ScoreRankingResponse

router = APIRouter()


@router.get("/map", response_model=ScoreMapResponse)
def score_map(
    energy: str = Query("ges", pattern="^(ges|res)$"),
    year: int = 2023,
    period: str = "annual",
):
    """Choropleth harita için ilçe başına agregalanmış skorları döner."""
    repo = get_repository()
    items = [ScoreMapItem(**r) for r in repo.score_map(energy, year)]
    return ScoreMapResponse(energy=energy, year=year, period=period, items=items)


@router.get("/ranking", response_model=ScoreRankingResponse)
def score_ranking(
    energy: str = Query("ges", pattern="^(ges|res)$"),
    year: int = 2023,
    limit: int = Query(10, ge=1, le=100),
):
    """En yüksek yıllık ortalamaya sahip ilçeleri döner."""
    repo = get_repository()
    items = [ScoreMapItem(**r) for r in repo.ranking(energy, limit, year)]
    return ScoreRankingResponse(energy=energy, year=year, items=items)
