"""Pydantic schemas for Movie endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class MovieBase(BaseModel):
    rank: int = Field(..., ge=1, description="IMDb Rank")
    title: str = Field(..., min_length=1, max_length=255, description="Movie Title")
    release_year: int = Field(..., ge=1888, le=2100, description="Release Year")
    imdb_rating: float = Field(..., ge=0.0, le=10.0, description="IMDb Rating between 0.0 and 10.0")
    votes: Optional[str] = Field("N/A", description="Formatted Votes count string")
    votes_count: Optional[int] = Field(0, description="Numeric votes count")
    poster_image: Optional[str] = Field("", description="Poster Image URL")
    imdb_link: Optional[str] = Field("#", description="IMDb Title URL")
    genre: Optional[str] = Field("Drama", description="Movie Primary Genre(s)")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Movie title cannot be empty")
        return trimmed


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    rank: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    release_year: Optional[int] = Field(None, ge=1888, le=2100)
    imdb_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    votes: Optional[str] = None
    votes_count: Optional[int] = None
    poster_image: Optional[str] = None
    imdb_link: Optional[str] = None
    genre: Optional[str] = None


class MovieResponse(BaseModel):
    id: int
    rank: int
    title: str
    release_year: int
    imdb_rating: float
    votes: str
    votes_count: int
    poster_image: str
    imdb_link: str
    genre: str

    class Config:
        from_attributes = True


class MovieListResponse(BaseModel):
    status: str = "success"
    count: int
    total: int
    page: int = 1
    limit: int = 250
    movies: List[dict]
