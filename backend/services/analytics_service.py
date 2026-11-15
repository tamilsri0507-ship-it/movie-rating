"""Analytics Service: Rating analytics, genre distribution, and decade analytics."""

import statistics
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.movie import Movie


def compute_summary_stats(db: Session) -> Dict[str, Any]:
    """Compute top-level dashboard metrics directly from SQLite database records."""
    movies = db.query(Movie).all()
    if not movies:
        return {
            "total_movies": 0,
            "avg_rating": 0.0,
            "top_movie": "N/A",
            "top_rating": 0.0,
            "top_decade": "N/A",
            "total_votes_approx": "0",
            "decades": {}
        }

    total = len(movies)
    ratings = [m.imdb_rating for m in movies if m.imdb_rating is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    # Top rated movie
    top_movie_obj = max(movies, key=lambda m: m.imdb_rating or 0.0)

    # Decades count
    decades_count: Dict[str, int] = {}
    total_votes = 0

    for m in movies:
        if m.release_year and len(str(m.release_year)) == 4:
            decade = f"{str(m.release_year)[:3]}0s"
            decades_count[decade] = decades_count.get(decade, 0) + 1
        total_votes += m.votes_count or 0

    top_decade = (
        max(decades_count.items(), key=lambda x: x[1])[0]
        if decades_count else "1990s"
    )

    return {
        "total_movies": total,
        "avg_rating": avg_rating,
        "top_movie": top_movie_obj.title,
        "top_rating": top_movie_obj.imdb_rating,
        "top_decade": top_decade,
        "total_votes_approx": f"{total_votes:,}",
        "decades": dict(sorted(decades_count.items()))
    }


def compute_decade_distribution(db: Session) -> List[Dict[str, Any]]:
    """Compute detailed era analytics per decade."""
    movies = db.query(Movie).all()
    decades_map: Dict[str, List[Movie]] = {}

    for m in movies:
        decade = f"{str(m.release_year)[:3]}0s"
        decades_map.setdefault(decade, []).append(m)

    results = []
    for decade, m_list in sorted(decades_map.items()):
        decade_ratings = [m.imdb_rating for m in m_list]
        avg_r = round(sum(decade_ratings) / len(decade_ratings), 2)
        best_m = max(m_list, key=lambda x: x.imdb_rating)

        results.append({
            "decade": decade,
            "count": len(m_list),
            "avg_rating": avg_r,
            "top_movie": best_m.title,
            "top_rating": best_m.imdb_rating
        })

    return results


def compute_genre_distribution(db: Session) -> List[Dict[str, Any]]:
    """Compute genre frequency distribution and average rating per genre."""
    movies = db.query(Movie).all()
    genre_movies: Dict[str, List[Movie]] = {}

    for m in movies:
        raw_genres = (m.genre or "Drama").split(",")
        for g in raw_genres:
            clean_g = g.strip()
            if clean_g:
                genre_movies.setdefault(clean_g, []).append(m)

    total_movies = len(movies) or 1
    genre_stats = []

    for genre, m_list in genre_movies.items():
        ratings = [m.imdb_rating for m in m_list]
        avg_r = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        best_m = max(m_list, key=lambda x: x.imdb_rating)

        genre_stats.append({
            "genre": genre,
            "count": len(m_list),
            "percentage": round((len(m_list) / total_movies) * 100, 1),
            "avg_rating": avg_r,
            "top_movie": best_m.title
        })

    # Sort descending by count
    genre_stats.sort(key=lambda x: x["count"], reverse=True)
    return genre_stats


def compute_rating_analytics(db: Session) -> Dict[str, Any]:
    """Compute statistical rating metrics and histogram distribution bins."""
    movies = db.query(Movie).all()
    if not movies:
        return {
            "total_movies": 0,
            "mean_rating": 0.0,
            "median_rating": 0.0,
            "std_dev": 0.0,
            "min_rating": 0.0,
            "max_rating": 0.0,
            "rating_bins": []
        }

    ratings = [m.imdb_rating for m in movies if m.imdb_rating is not None]
    total = len(ratings)

    mean_val = round(statistics.mean(ratings), 2)
    median_val = round(statistics.median(ratings), 2)
    std_val = round(statistics.stdev(ratings), 2) if total > 1 else 0.0
    min_val = min(ratings)
    max_val = max(ratings)

    # Binning
    bins = [
        {"label": "9.0 - 10.0 (Masterpieces)", "min_rating": 9.0, "max_rating": 10.0, "count": 0},
        {"label": "8.5 - 8.9 (Critically Acclaimed)", "min_rating": 8.5, "max_rating": 8.99, "count": 0},
        {"label": "8.0 - 8.4 (Great Classics)", "min_rating": 8.0, "max_rating": 8.49, "count": 0},
        {"label": "< 8.0 (Honorable Mentions)", "min_rating": 0.0, "max_rating": 7.99, "count": 0},
    ]

    for r in ratings:
        for b in bins:
            if b["min_rating"] <= r <= b["max_rating"]:
                b["count"] += 1
                break

    for b in bins:
        b["percentage"] = round((b["count"] / total) * 100, 1)

    return {
        "total_movies": total,
        "mean_rating": mean_val,
        "median_rating": median_val,
        "std_dev": std_val,
        "min_rating": min_val,
        "max_rating": max_val,
        "rating_bins": bins
    }
