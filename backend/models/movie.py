"""SQLAlchemy model for Movie records."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rank = Column(Integer, index=True, nullable=False)
    title = Column(String(255), index=True, nullable=False)
    release_year = Column(Integer, index=True, nullable=False)
    imdb_rating = Column(Float, index=True, nullable=False)
    votes = Column(String(64), nullable=True, default="N/A")
    votes_count = Column(Integer, index=True, default=0)
    poster_image = Column(String(512), nullable=True, default="")
    imdb_link = Column(String(512), nullable=True, default="#")
    genre = Column(String(128), index=True, nullable=True, default="Drama")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary matching frontend format."""
        return {
            "id": self.id,
            "Rank": self.rank,
            "Title": self.title,
            "Release Year": self.release_year,
            "IMDb Rating": self.imdb_rating,
            "Votes": self.votes,
            "Votes Count": self.votes_count,
            "Poster Image": self.poster_image,
            "IMDb Link": self.imdb_link,
            "Genre": self.genre,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
