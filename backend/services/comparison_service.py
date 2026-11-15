"""Movie Comparison Service: Head-to-head comparison between two movies."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.models.movie import Movie
from backend.services.ai_recommender import AIRecommender


def compare_two_movies(db: Session, movie1_id: int, movie2_id: int) -> Optional[Dict[str, Any]]:
    """Compare two movie records side by side with statistical and AI metrics."""
    m1 = db.query(Movie).filter((Movie.id == movie1_id) | (Movie.rank == movie1_id)).first()
    m2 = db.query(Movie).filter((Movie.id == movie2_id) | (Movie.rank == movie2_id)).first()

    if not m1 or not m2:
        return None

    # Rating comparison
    rating_diff = round(abs(m1.imdb_rating - m2.imdb_rating), 2)
    if m1.imdb_rating > m2.imdb_rating:
        rating_winner = m1.title
    elif m2.imdb_rating > m1.imdb_rating:
        rating_winner = m2.title
    else:
        rating_winner = "Tie (Equal Rating)"

    # Votes comparison
    votes_diff = abs((m1.votes_count or 0) - (m2.votes_count or 0))
    if (m1.votes_count or 0) > (m2.votes_count or 0):
        votes_winner = m1.title
    elif (m2.votes_count or 0) > (m1.votes_count or 0):
        votes_winner = m2.title
    else:
        votes_winner = "Tie"

    # Year gap
    year_gap = abs(m1.release_year - m2.release_year)

    # Shared genres
    g1 = set(g.strip() for g in (m1.genre or "Drama").split(","))
    g2 = set(g.strip() for g in (m2.genre or "Drama").split(","))
    shared_genres = sorted(list(g1 & g2))

    # Compute AI Cosine Similarity between the two movies
    feat1 = AIRecommender.build_content_feature(m1)
    feat2 = AIRecommender.build_content_feature(m2)

    vec = TfidfVectorizer(stop_words="english")
    tfidf = vec.fit_transform([feat1, feat2])
    sim = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    sim_percent = f"{round(sim * 100, 1)}%"

    # Construct verdict
    verdict_parts = []
    if m1.imdb_rating != m2.imdb_rating:
        winner = m1 if m1.imdb_rating > m2.imdb_rating else m2
        loser = m2 if m1.imdb_rating > m2.imdb_rating else m1
        verdict_parts.append(
            f"'{winner.title}' holds a higher IMDb rating of {winner.imdb_rating} vs {loser.imdb_rating} (+{rating_diff})."
        )
    else:
        verdict_parts.append(f"Both films boast an identical IMDb rating of {m1.imdb_rating}.")

    if year_gap > 0:
        older = m1 if m1.release_year < m2.release_year else m2
        newer = m2 if m1.release_year < m2.release_year else m1
        verdict_parts.append(f"'{older.title}' was released {year_gap} years prior to '{newer.title}'.")

    if shared_genres:
        verdict_parts.append(f"Both masterpieces share common genre DNA: {', '.join(shared_genres)}.")

    verdict_parts.append(f"Content similarity index stands at {sim_percent}.")
    verdict = " ".join(verdict_parts)

    metrics_table = [
        {"metric": "IMDb Rating", "movie1_value": str(m1.imdb_rating), "movie2_value": str(m2.imdb_rating), "advantage": rating_winner},
        {"metric": "IMDb Rank", "movie1_value": f"#{m1.rank}", "movie2_value": f"#{m2.rank}", "advantage": m1.title if m1.rank < m2.rank else m2.title},
        {"metric": "Release Year", "movie1_value": str(m1.release_year), "movie2_value": str(m2.release_year), "advantage": f"{year_gap} yr gap"},
        {"metric": "Total Votes", "movie1_value": m1.votes, "movie2_value": m2.votes, "advantage": votes_winner},
        {"metric": "Genres", "movie1_value": m1.genre, "movie2_value": m2.genre, "advantage": f"{len(shared_genres)} shared"},
        {"metric": "AI Content Match", "movie1_value": sim_percent, "movie2_value": sim_percent, "advantage": "Similarity Index"},
    ]

    return {
        "status": "success",
        "movie1": m1.to_dict(),
        "movie2": m2.to_dict(),
        "rating_diff": rating_diff,
        "rating_winner": rating_winner,
        "votes_diff": votes_diff,
        "votes_winner": votes_winner,
        "year_gap": year_gap,
        "cosine_similarity": round(sim, 4),
        "similarity_percentage": sim_percent,
        "shared_genres": shared_genres,
        "verdict": verdict,
        "metrics_table": metrics_table
    }
