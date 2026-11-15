"""AI Movie Recommendation Router using Scikit-Learn TF-IDF and Cosine Similarity."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.ai_recommender import ai_recommender

router = APIRouter(prefix="/api/recommendations", tags=["AI Recommendations"])


@router.get("/{movie_id}", summary="Get AI-powered recommendations for a movie")
def get_recommendations(
    movie_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations to return"),
    db: Session = Depends(get_db)
):
    """
    Computes genuine TF-IDF feature matrices and Cosine Similarities across all 
    database movies, returning the highest-scoring recommendations with match percentages 
    and feature explanation tags.
    """
    result = ai_recommender.get_recommendations(db=db, target_movie_id=movie_id, top_n=limit)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target movie ID {movie_id} was not found to generate recommendations."
        )

    return {
        "status": "success",
        "algorithm": "Scikit-Learn TF-IDF Vectorizer + Cosine Similarity",
        **result
    }
