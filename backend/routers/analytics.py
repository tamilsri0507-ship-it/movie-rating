"""Analytics, Decades, Genres, and Rating Metrics Router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.analytics_service import (
    compute_summary_stats,
    compute_decade_distribution,
    compute_genre_distribution,
    compute_rating_analytics
)

router = APIRouter(tags=["Analytics"])


@router.get("/api/stats", summary="Legacy dashboard summary statistics")
def get_stats(db: Session = Depends(get_db)):
    """Fetch high-level dashboard metrics (Total Movies, Top Movie, Avg Rating, Decades)."""
    stats = compute_summary_stats(db)
    return {"status": "success", "stats": stats}


@router.get("/api/analytics/summary", summary="Complete summary statistics")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Fetch structured summary metrics."""
    stats = compute_summary_stats(db)
    return {"status": "success", "summary": stats}


@router.get("/api/analytics/decades", summary="Decade distribution breakdown")
def get_decades_analytics(db: Session = Depends(get_db)):
    """Fetch decade distribution, average rating per decade, and best films."""
    decades = compute_decade_distribution(db)
    return {"status": "success", "decades": decades}


@router.get("/api/analytics/genres", summary="Genre distribution breakdown")
def get_genres_analytics(db: Session = Depends(get_db)):
    """Fetch genre frequency counts, market share, and average ratings."""
    genres = compute_genre_distribution(db)
    return {"status": "success", "total_genres": len(genres), "genres": genres}


@router.get("/api/analytics/ratings", summary="Rating statistics & histogram distribution")
def get_ratings_analytics(db: Session = Depends(get_db)):
    """Statistical summary (mean, median, std dev, min, max, rating histogram bins)."""
    ratings_info = compute_rating_analytics(db)
    return {"status": "success", **ratings_info}
