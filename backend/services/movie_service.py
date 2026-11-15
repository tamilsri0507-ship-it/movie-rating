"""Movie CRUD, Search, Filter, Sort and Seeding Service."""

import os
import re
import csv
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.models.movie import Movie
from backend.schemas.movie import MovieCreate, MovieUpdate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_FILEPATH = os.path.join(BASE_DIR, "imdb_top_250.csv")

# Known genre classification mapping for IMDb Top 250 movies
GENRE_MAP = {
    "The Shawshank Redemption": "Drama",
    "The Godfather": "Crime, Drama",
    "The Dark Knight": "Action, Crime, Drama",
    "The Godfather Part II": "Crime, Drama",
    "12 Angry Men": "Crime, Drama",
    "Schindler's List": "Biography, Drama, History",
    "The Lord of the Rings: The Return of the King": "Action, Adventure, Drama",
    "Pulp Fiction": "Crime, Drama",
    "The Lord of the Rings: The Fellowship of the Ring": "Action, Adventure, Drama",
    "The Good, the Bad and the Ugly": "Western, Adventure",
    "Forrest Gump": "Drama, Romance",
    "Fight Club": "Drama, Thriller",
    "Inception": "Action, Adventure, Sci-Fi",
    "The Lord of the Rings: The Two Towers": "Action, Adventure, Drama",
    "Star Wars: Episode V - The Empire Strikes Back": "Action, Adventure, Fantasy",
    "The Matrix": "Action, Sci-Fi",
    "Goodfellas": "Biography, Crime, Drama",
    "One Flew Over the Cuckoo's Nest": "Drama",
    "Interstellar": "Adventure, Drama, Sci-Fi",
    "Seven": "Crime, Drama, Mystery",
    "It's a Wonderful Life": "Drama, Family, Fantasy",
    "The Silence of the Lambs": "Crime, Drama, Thriller",
    "Saving Private Ryan": "Drama, War",
    "City of God": "Crime, Drama",
    "Life Is Beautiful": "Comedy, Drama, Romance",
    "Spirited Away": "Animation, Adventure, Family",
    "The Green Mile": "Crime, Drama, Fantasy",
    "Star Wars: Episode IV - A New Hope": "Action, Adventure, Fantasy",
    "Terminator 2: Judgment Day": "Action, Sci-Fi",
    "Back to the Future": "Adventure, Comedy, Sci-Fi",
    "Spiderman: Into the Spider-Verse": "Animation, Action, Adventure",
    "Alien": "Horror, Sci-Fi",
    "Psycho": "Horror, Mystery, Thriller",
    "The Pianist": "Biography, Drama, Music",
    "Parasite": "Drama, Thriller",
    "Whiplash": "Drama, Music",
    "Gladiator": "Action, Adventure, Drama",
    "The Prestige": "Drama, Mystery, Sci-Fi",
    "The Departed": "Crime, Drama, Thriller",
    "Memento": "Mystery, Thriller",
    "Apocalypse Now": "Drama, Mystery, War",
    "Django Unchained": "Drama, Western",
    "WALL-E": "Animation, Adventure, Family",
    "The Lives of Others": "Drama, Mystery, Thriller",
    "Sunset Boulevard": "Drama, Film-Noir",
    "Paths of Glory": "Drama, War",
    "The Shining": "Drama, Horror",
    "The Great Dictator": "Comedy, Drama, War",
    "Avengers: Infinity War": "Action, Adventure, Sci-Fi",
    "Witness for the Prosecution": "Crime, Drama, Mystery",
    "Aliens": "Action, Adventure, Sci-Fi",
    "Spider-Man: Across the Spider-Verse": "Animation, Action, Adventure",
    "Oppenheimer": "Biography, Drama, History",
    "American History X": "Crime, Drama",
    "The Dark Knight Rises": "Action, Drama, Thriller",
    "Oldboy": "Action, Drama, Mystery",
    "Joker": "Crime, Drama, Thriller",
    "Amadeus": "Biography, Drama, Music",
    "Braveheart": "Biography, Drama, History",
    "Toy Story": "Animation, Adventure, Comedy",
    "Coco": "Animation, Adventure, Family",
    "Avengers: Endgame": "Action, Adventure, Drama",
    "Inglourious Basterds": "Adventure, Drama, War",
    "Princess Mononoke": "Animation, Action, Adventure",
    "Good Will Hunting": "Drama, Romance",
    "Once Upon a Time in America": "Crime, Drama",
    "Requiem for a Dream": "Drama",
    "Toy Story 3": "Animation, Adventure, Comedy",
    "Your Name.": "Animation, Drama, Fantasy",
    "3 Idiots": "Comedy, Drama",
    "Dangal": "Action, Biography, Drama",
    "Taare Zameen Par": "Drama, Family",
    "Gangs of Wasseypur": "Action, Comedy, Crime",
    "Lagaan: Once Upon a Time in India": "Adventure, Drama, Musical"
}


def parse_vote_number(vote_str: str) -> int:
    """Extract numeric vote count from string like '2,900,000'."""
    if not vote_str or vote_str == "N/A":
        return 0
    clean = re.sub(r"[^\d]", "", str(vote_str))
    try:
        return int(clean) if clean else 0
    except ValueError:
        return 0


def determine_genre(title: str, existing_genre: Optional[str] = None) -> str:
    """Return specific genre if mapped, otherwise infer or default."""
    if title in GENRE_MAP:
        return GENRE_MAP[title]
    if existing_genre and existing_genre.strip() and existing_genre.strip() != "N/A":
        return existing_genre.strip()

    title_lower = title.lower()
    if any(k in title_lower for k in ["star wars", "alien", "matrix", "spider", "avenger", "terminator", "dark knight", "batman", "blade"]):
        return "Action, Sci-Fi"
    if any(k in title_lower for k in ["lord of the rings", "indiana jones", "adventure", "potter", "future"]):
        return "Adventure, Fantasy"
    if any(k in title_lower for k in ["godfather", "crime", "goodfellas", "mafia", "detective", "pulp"]):
        return "Crime, Drama"
    if any(k in title_lower for k in ["toy story", "spirited", "lion king", "nemo", "coco", "up", "mononoke", "animation"]):
        return "Animation, Adventure"
    if any(k in title_lower for k in ["psycho", "shining", "horror", "quiet", "zombie"]):
        return "Horror, Mystery"
    if any(k in title_lower for k in ["schindler", "biography", "pianist", "oppenheimer", "amadeus"]):
        return "Biography, Drama"
    if any(k in title_lower for k in ["comedy", "dictator", "monty", "lebowski"]):
        return "Comedy, Drama"
    return "Drama"


def seed_initial_dataset(db: Session, force: bool = False) -> int:
    """
    Ensure exactly 250 sample records are in SQLite database for demo mode.
    Reads from imdb_top_250.csv if present.
    """
    count = db.query(Movie).count()
    if count >= 250 and not force:
        return count

    movies_to_insert = []
    if os.path.exists(CSV_FILEPATH):
        with open(CSV_FILEPATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                title = row.get("Title", f"Movie #{idx}").strip()
                try:
                    rank = int(row.get("Rank", idx))
                except (ValueError, TypeError):
                    rank = idx

                try:
                    year = int(row.get("Release Year", 2000))
                except (ValueError, TypeError):
                    year = 2000

                try:
                    rating = float(row.get("IMDb Rating", 8.0))
                except (ValueError, TypeError):
                    rating = 8.0

                votes_str = str(row.get("Votes", "100,000"))
                votes_num = parse_vote_number(votes_str)
                poster = row.get("Poster Image", "")
                link = row.get("IMDb Link", "#")
                genre = determine_genre(title, row.get("Genre", None))

                movies_to_insert.append(
                    Movie(
                        rank=rank,
                        title=title,
                        release_year=year,
                        imdb_rating=rating,
                        votes=votes_str,
                        votes_count=votes_num,
                        poster_image=poster,
                        imdb_link=link,
                        genre=genre,
                    )
                )

    if movies_to_insert:
        if force:
            db.query(Movie).delete()
            db.commit()

        # Insert only missing records if not forced
        if not force:
            existing_ranks = set(r[0] for r in db.query(Movie.rank).all())
            to_add = [m for m in movies_to_insert if m.rank not in existing_ranks]
            if to_add:
                db.bulk_save_objects(to_add)
                db.commit()
        else:
            db.bulk_save_objects(movies_to_insert)
            db.commit()

    return db.query(Movie).count()


def get_all_movies(
    db: Session,
    skip: int = 0,
    limit: int = 250,
    search: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    genre: Optional[str] = None,
    decade: Optional[str] = None,
    sort_by: str = "rank",
    order: str = "asc",
) -> Tuple[List[Movie], int]:
    """Search, filter, sort and paginate movies."""
    query = db.query(Movie)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Movie.title.ilike(search_term),
                Movie.genre.ilike(search_term),
                Movie.release_year.cast(Movie.title.type).ilike(search_term),
            )
        )

    if min_rating is not None and min_rating > 0:
        query = query.filter(Movie.imdb_rating >= min_rating)

    if max_rating is not None and max_rating <= 10:
        query = query.filter(Movie.imdb_rating <= max_rating)

    if genre and genre != "All":
        query = query.filter(Movie.genre.ilike(f"%{genre}%"))

    if decade and decade != "All":
        clean_decade = decade.replace("s", "").strip()
        if clean_decade.isdigit() and len(clean_decade) == 4:
            start_year = int(clean_decade)
            end_year = start_year + 9
            query = query.filter(Movie.release_year.between(start_year, end_year))

    total = query.count()

    # Sorting logic
    sort_field = {
        "rank": Movie.rank,
        "rating": Movie.imdb_rating,
        "year": Movie.release_year,
        "title": Movie.title,
        "votes": Movie.votes_count,
    }.get(sort_by.lower(), Movie.rank)

    if order.lower() == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))

    movies = query.offset(skip).limit(limit).all()
    return movies, total


def get_movie_by_id(db: Session, movie_id: int) -> Optional[Movie]:
    return db.query(Movie).filter(Movie.id == movie_id).first()


def get_movie_by_rank(db: Session, rank: int) -> Optional[Movie]:
    return db.query(Movie).filter(Movie.rank == rank).first()


def get_movie_by_title(db: Session, title: str) -> Optional[Movie]:
    return db.query(Movie).filter(Movie.title.ilike(title.strip())).first()


def create_movie(db: Session, movie_in: MovieCreate) -> Movie:
    votes_num = movie_in.votes_count or parse_vote_number(movie_in.votes)
    genre = determine_genre(movie_in.title, movie_in.genre)

    movie = Movie(
        rank=movie_in.rank,
        title=movie_in.title,
        release_year=movie_in.release_year,
        imdb_rating=movie_in.imdb_rating,
        votes=movie_in.votes,
        votes_count=votes_num,
        poster_image=movie_in.poster_image or "",
        imdb_link=movie_in.imdb_link or "#",
        genre=genre,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def update_movie(db: Session, movie_id: int, movie_in: MovieUpdate) -> Optional[Movie]:
    movie = get_movie_by_id(db, movie_id)
    if not movie:
        return None

    update_data = movie_in.model_dump(exclude_unset=True)
    if "votes" in update_data and "votes_count" not in update_data:
        update_data["votes_count"] = parse_vote_number(update_data["votes"])

    for field, val in update_data.items():
        setattr(movie, field, val)

    db.commit()
    db.refresh(movie)
    return movie


def delete_movie(db: Session, movie_id: int) -> bool:
    movie = get_movie_by_id(db, movie_id)
    if not movie:
        return False
    db.delete(movie)
    db.commit()
    return True
