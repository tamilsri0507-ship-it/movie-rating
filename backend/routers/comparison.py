"""Movie Comparison Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.comparison_service import compare_two_movies

router = APIRouter(tags=["Movie Comparison"])


class CompareRequest(BaseModel):
    movie1_id: int
    movie2_id: int


@router.get("/api/movies/compare", summary="Compare two movies side by side")
@router.get("/api/compare", summary="Compare two movies side by side (alias)")
def compare_movies_get(
    movie1_id: int = Query(..., description="ID or Rank of first movie"),
    movie2_id: int = Query(..., description="ID or Rank of second movie"),
    db: Session = Depends(get_db)
):
    """Perform statistical and AI cosine similarity comparison between two films."""
    if movie1_id == movie2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a movie to itself. Please provide two distinct movie IDs."
        )

    res = compare_two_movies(db, movie1_id, movie2_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both movies could not be found."
        )
    return res


@router.post("/api/movies/compare", summary="Compare two movies via POST body")
@router.post("/api/compare", summary="Compare two movies via POST body (alias)")
def compare_movies_post(payload: CompareRequest, db: Session = Depends(get_db)):
    """Perform comparison via JSON payload."""
    if payload.movie1_id == payload.movie2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a movie to itself. Please provide two distinct movie IDs."
        )

    res = compare_two_movies(db, payload.movie1_id, payload.movie2_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both movies could not be found."
        )
    return res
