"""Pydantic schemas for Movie Comparison."""

from typing import List, Optional
from pydantic import BaseModel


class ComparisonMetric(BaseModel):
    metric: str
    movie1_value: str
    movie2_value: str
    advantage: str


class MovieComparisonResponse(BaseModel):
    status: str = "success"
    movie1: dict
    movie2: dict
    rating_diff: float
    rating_winner: str
    votes_diff: int
    votes_winner: str
    year_gap: int
    cosine_similarity: float
    similarity_percentage: str
    shared_genres: List[str]
    verdict: str
    metrics_table: List[ComparisonMetric]
