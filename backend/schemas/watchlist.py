"""Pydantic schemas for Watchlist management."""

from typing import List, Optional
from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    movie_id: int = Field(..., ge=1, description="Movie ID to add to watchlist")
    notes: Optional[str] = Field("", max_length=500, description="Personal viewer notes")
    priority: Optional[str] = Field("Normal", description="Priority level: High, Normal, Low")


class WatchlistResponse(BaseModel):
    status: str = "success"
    count: int
    watchlist: List[dict]


class WatchlistCheckResponse(BaseModel):
    movie_id: int
    is_in_watchlist: bool
    watchlist_id: Optional[int] = None
