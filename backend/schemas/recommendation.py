"""Pydantic schemas for AI Movie Recommendations."""

from typing import List, Optional
from pydantic import BaseModel


class RecommendedMovieItem(BaseModel):
    id: int
    rank: int
    title: str
    release_year: int
    imdb_rating: float
    poster_image: str
    imdb_link: str
    genre: str
    similarity_score: float
    match_percentage: str
    explanation: str


class RecommendationResponse(BaseModel):
    status: str = "success"
    algorithm: str = "TF-IDF Vectorizer + Cosine Similarity"
    target_movie_id: int
    target_movie_title: str
    count: int
    recommendations: List[RecommendedMovieItem]
