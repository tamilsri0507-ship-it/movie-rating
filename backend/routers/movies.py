"""Movie CRUD, Search, Filter, and Sort Router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.movie import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    MovieListResponse
)
from backend.services.movie_service import (
    get_all_movies,
    get_movie_by_id,
    create_movie,
    update_movie,
    delete_movie
)

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.get("", response_model=MovieListResponse, summary="List movies with search, filter, and sort")
def list_movies(
    search: Optional[str] = Query(None, description="Search term for title or genre"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum IMDb rating"),
    max_rating: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum IMDb rating"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., Drama, Action, Sci-Fi)"),
    decade: Optional[str] = Query(None, description="Filter by decade (e.g., 1990s, 2000s)"),
    sort_by: str = Query("rank", description="Field to sort by: rank, rating, year, title, votes"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(250, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve movies matching query criteria with pagination and metadata."""
    skip = (page - 1) * limit
    movies, total = get_all_movies(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        min_rating=min_rating,
        max_rating=max_rating,
        genre=genre,
        decade=decade,
        sort_by=sort_by,
        order=order
    )
    return {
        "status": "success",
        "count": len(movies),
        "total": total,
        "page": page,
        "limit": limit,
        "movies": [m.to_dict() for m in movies]
    }


@router.get("/{movie_id}", summary="Get movie details by ID")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Retrieve a single movie record by its database ID or Rank."""
    movie = get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found."
        )
    return {"status": "success", "movie": movie.to_dict()}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create new movie record")
def add_movie(movie_in: MovieCreate, db: Session = Depends(get_db)):
    """Add a new movie record into the database."""
    movie = create_movie(db, movie_in)
    return {
        "status": "success",
        "message": f"Movie '{movie.title}' created successfully.",
        "movie": movie.to_dict()
    }


@router.put("/{movie_id}", summary="Update movie record")
def edit_movie(movie_id: int, movie_in: MovieUpdate, db: Session = Depends(get_db)):
    """Update fields of an existing movie."""
    movie = update_movie(db, movie_id, movie_in)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found."
        )
    return {
        "status": "success",
        "message": f"Movie '{movie.title}' updated successfully.",
        "movie": movie.to_dict()
    }


@router.delete("/{movie_id}", summary="Delete movie record")
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    """Remove a movie from database."""
    success = delete_movie(db, movie_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found."
        )
    return {
        "status": "success",
        "message": f"Movie with ID {movie_id} deleted successfully."
    }
