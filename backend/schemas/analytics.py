"""Pydantic schemas for Analytics and Statistics."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class SummaryStats(BaseModel):
    total_movies: int
    avg_rating: float
    top_movie: str
    top_rating: float
    top_decade: str
    total_votes_approx: str
    decades: Dict[str, int]


class DecadeStatItem(BaseModel):
    decade: str
    count: int
    avg_rating: float
    top_movie: str
    top_rating: float


class GenreStatItem(BaseModel):
    genre: str
    count: int
    percentage: float
    avg_rating: float
    top_movie: str


class RatingBinItem(BaseModel):
    label: str
    min_rating: float
    max_rating: float
    count: int
    percentage: float


class RatingAnalyticsResponse(BaseModel):
    status: str = "success"
    total_movies: int
    mean_rating: float
    median_rating: float
    std_dev: float
    min_rating: float
    max_rating: float
    rating_bins: List[RatingBinItem]


class GenreAnalyticsResponse(BaseModel):
    status: str = "success"
    total_movies: int
    genres: List[GenreStatItem]


class DecadeAnalyticsResponse(BaseModel):
    status: str = "success"
    decades: List[DecadeStatItem]
