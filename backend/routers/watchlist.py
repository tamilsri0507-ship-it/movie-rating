"""Watchlist Router for user movie bookmarks."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.watchlist_service import (
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    is_in_watchlist
)

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


class WatchlistAddPayload(BaseModel):
    notes: Optional[str] = ""
    priority: Optional[str] = "Normal"


@router.get("", summary="Get all watchlisted movies")
def list_watchlist(db: Session = Depends(get_db)):
    """Retrieve all movies saved in the user's personal watchlist."""
    items = get_watchlist(db)
    return {
        "status": "success",
        "count": len(items),
        "watchlist": items
    }


@router.post("/{movie_id}", status_code=status.HTTP_201_CREATED, summary="Add movie to watchlist")
def add_movie_watchlist(
    movie_id: int,
    payload: Optional[WatchlistAddPayload] = None,
    db: Session = Depends(get_db)
):
    """Save a movie to watchlist with optional notes and priority."""
    notes = payload.notes if payload else ""
    priority = payload.priority if payload else "Normal"

    item = add_to_watchlist(db, movie_id, notes=notes, priority=priority)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} does not exist to add to watchlist."
        )

    return {
        "status": "success",
        "message": f"Movie successfully added to your watchlist.",
        "item": item.to_dict()
    }


@router.delete("/{movie_id}", summary="Remove movie from watchlist")
def remove_movie_watchlist(movie_id: int, db: Session = Depends(get_db)):
    """Remove a movie or watchlist entry from watchlist."""
    success = remove_from_watchlist(db, movie_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} was not found in your watchlist."
        )

    return {
        "status": "success",
        "message": "Movie successfully removed from your watchlist."
    }


@router.get("/check/{movie_id}", summary="Check if a movie is in watchlist")
def check_movie_watchlist(movie_id: int, db: Session = Depends(get_db)):
    """Quick lookup to see if a movie card is bookmarked."""
    return is_in_watchlist(db, movie_id)
