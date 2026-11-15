"""Watchlist Service for user movie bookmarks."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.watchlist import WatchlistItem
from backend.models.movie import Movie


def get_watchlist(db: Session) -> List[Dict[str, Any]]:
    """Retrieve all watchlisted movies."""
    items = db.query(WatchlistItem).order_by(WatchlistItem.added_at.desc()).all()
    return [item.to_dict() for item in items]


def add_to_watchlist(db: Session, movie_id: int, notes: str = "", priority: str = "Normal") -> Optional[WatchlistItem]:
    """Add a movie to user's watchlist."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        return None

    existing = db.query(WatchlistItem).filter(WatchlistItem.movie_id == movie_id).first()
    if existing:
        existing.notes = notes or existing.notes
        existing.priority = priority or existing.priority
        db.commit()
        db.refresh(existing)
        return existing

    item = WatchlistItem(movie_id=movie_id, notes=notes, priority=priority)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_watchlist(db: Session, movie_id: int) -> bool:
    """Remove a movie from user's watchlist."""
    item = db.query(WatchlistItem).filter(
        (WatchlistItem.movie_id == movie_id) | (WatchlistItem.id == movie_id)
    ).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def is_in_watchlist(db: Session, movie_id: int) -> Dict[str, Any]:
    """Check if a specific movie is already bookmarked."""
    item = db.query(WatchlistItem).filter(WatchlistItem.movie_id == movie_id).first()
    return {
        "movie_id": movie_id,
        "is_in_watchlist": item is not None,
        "watchlist_id": item.id if item else None
    }
