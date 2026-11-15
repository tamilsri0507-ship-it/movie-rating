"""SQLAlchemy model for user Watchlist."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    notes = Column(String(500), nullable=True, default="")
    priority = Column(String(32), nullable=True, default="Normal")
    added_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", backref="watchlist_entry", lazy="joined")

    def to_dict(self):
        movie_dict = self.movie.to_dict() if self.movie else {}
        return {
            "id": self.id,
            "movie_id": self.movie_id,
            "notes": self.notes,
            "priority": self.priority,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "movie": movie_dict,
        }
