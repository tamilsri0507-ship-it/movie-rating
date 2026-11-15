"""AI Movie Recommendation Engine using Scikit-Learn TF-IDF Vectorizer and Cosine Similarity."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.models.movie import Movie


class AIRecommender:
    """Computes genuine TF-IDF feature matrices and Cosine Similarities across movies."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[\w-]+\b",
            min_df=1
        )

    @staticmethod
    def build_content_feature(movie: Movie) -> str:
        """Create a multi-dimensional textual feature representation for TF-IDF."""
        decade = f"{str(movie.release_year)[:3]}0s"
        rating_tier = "legendary-tier" if movie.imdb_rating >= 9.0 else (
            "masterpiece-tier" if movie.imdb_rating >= 8.5 else "acclaimed-tier"
        )
        popularity = "mega-blockbuster" if movie.votes_count >= 1500000 else (
            "blockbuster" if movie.votes_count >= 800000 else "classic"
        )

        genre_tokens = " ".join([g.strip().lower() for g in (movie.genre or "Drama").split(",")])

        # Combine title tokens, genres, decade, rating caliber and popularity
        return (
            f"{movie.title.lower()} {genre_tokens} {genre_tokens} "
            f"{decade} {decade} {rating_tier} {popularity}"
        )

    def get_recommendations(
        self,
        db: Session,
        target_movie_id: int,
        top_n: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate cosine similarity matrix and return top N recommended movies
        with similarity scores and explanation breakdown.
        """
        all_movies = db.query(Movie).all()
        if not all_movies:
            return None

        # Find target movie
        target_movie = None
        target_idx = -1
        for idx, m in enumerate(all_movies):
            if m.id == target_movie_id or m.rank == target_movie_id:
                target_movie = m
                target_idx = idx
                break

        if not target_movie:
            return None

        # Build feature corpus
        corpus = [self.build_content_feature(m) for m in all_movies]

        # Compute TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # Compute Cosine Similarity between target movie vector and all movie vectors
        target_vector = tfidf_matrix[target_idx]
        similarity_scores = cosine_similarity(target_vector, tfidf_matrix)[0]

        # Pair movies with similarity scores
        scored_movies = []
        for idx, score in enumerate(similarity_scores):
            if idx == target_idx:
                continue  # Skip target movie itself
            scored_movies.append((all_movies[idx], float(score)))

        # Sort descending by similarity score
        scored_movies.sort(key=lambda x: x[1], reverse=True)

        # Format top N recommendations
        recommendations = []
        for m, score in scored_movies[:top_n]:
            percentage = round(score * 100, 1)

            # Generate insightful explanation tag
            shared_genres = set(g.strip() for g in (target_movie.genre or "").split(",")) & set(
                g.strip() for g in (m.genre or "").split(",")
            )
            genre_expl = f"Shared {', '.join(shared_genres)}" if shared_genres else "Similar Genre"

            target_decade = f"{str(target_movie.release_year)[:3]}0s"
            m_decade = f"{str(m.release_year)[:3]}0s"
            era_expl = f"Same {target_decade} Era" if target_decade == m_decade else f"{m_decade} Era"

            explanation = f"{genre_expl} • {era_expl} • Rating {m.imdb_rating}"

            recommendations.append({
                "id": m.id,
                "rank": m.rank,
                "title": m.title,
                "release_year": m.release_year,
                "imdb_rating": m.imdb_rating,
                "votes": m.votes,
                "poster_image": m.poster_image,
                "imdb_link": m.imdb_link,
                "genre": m.genre or "Drama",
                "similarity_score": round(score, 4),
                "match_percentage": f"{percentage}%",
                "explanation": explanation
            })

        return {
            "target_movie_id": target_movie.id,
            "target_movie_title": target_movie.title,
            "count": len(recommendations),
            "recommendations": recommendations
        }


# Singleton instance
ai_recommender = AIRecommender()
