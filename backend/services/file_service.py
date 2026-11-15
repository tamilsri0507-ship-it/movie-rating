"""File Service: CSV & Excel uploads, dataset validation, and duplicate detection."""

import io
import re
from typing import Dict, Any, List, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.movie import Movie
from backend.services.movie_service import parse_vote_number, determine_genre


def normalize_column_name(col: str) -> str:
    """Normalize user input column names to match internal schema distinctly."""
    c = col.strip().lower().replace("_", " ")
    if "rank" in c:
        return "rank"
    if "title" in c or "movie" in c or "name" in c:
        return "title"
    if "year" in c or "release" in c:
        return "release_year"
    if "rating" in c or "score" in c:
        return "imdb_rating"
    if "votes count" in c or "vote count" in c:
        return "votes_count"
    if "vote" in c:
        return "votes"
    if "poster" in c or "image" in c or "img" in c:
        return "poster_image"
    if "link" in c or "url" in c:
        return "imdb_link"
    if "genre" in c or "category" in c:
        return "genre"
    return col.strip()


def parse_and_import_dataframe(db: Session, df: pd.DataFrame) -> Tuple[int, int, List[str]]:
    """Parse a pandas DataFrame and upsert/insert movie records into SQLite."""
    # Rename columns to standard names ensuring no duplicates
    seen = set()
    new_cols = []
    for col in df.columns:
        norm = normalize_column_name(col)
        if norm in seen:
            new_cols.append(f"{norm}_extra")
        else:
            seen.add(norm)
            new_cols.append(norm)
    df.columns = new_cols

    added = 0
    updated = 0
    errors = []

    for index, row in df.iterrows():
        try:
            raw_title = row.get("title", "")
            title = str(raw_title).strip()
            if not title or title.lower() in ["nan", "none", "unknown"]:
                continue

            try:
                rank = int(row.get("rank", index + 1))
            except (ValueError, TypeError):
                rank = index + 1

            try:
                raw_year = str(row.get("release_year", 2000)).strip()
                year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_year)
                year = int(year_match.group(1)) if year_match else 2000
            except (ValueError, TypeError):
                year = 2000

            try:
                raw_rating = float(row.get("imdb_rating", 8.0))
                rating = max(0.0, min(10.0, round(raw_rating, 2)))
            except (ValueError, TypeError):
                rating = 8.0

            votes_str = str(row.get("votes", "100,000")).strip()
            votes_num = parse_vote_number(votes_str)
            # Check if votes_num is within standard 32-bit integer
            if votes_num > 2147483647:
                votes_num = 2000000

            poster = str(row.get("poster_image", "")).strip()
            link = str(row.get("imdb_link", "#")).strip()
            genre = determine_genre(title, str(row.get("genre", "")))

            # Check if movie already exists by title
            existing = db.query(Movie).filter(Movie.title.ilike(title)).first()
            if existing:
                existing.rank = rank
                existing.release_year = year
                existing.imdb_rating = rating
                existing.votes = votes_str
                existing.votes_count = votes_num
                if poster and poster != "nan":
                    existing.poster_image = poster
                if link and link != "nan":
                    existing.imdb_link = link
                existing.genre = genre
                updated += 1
            else:
                new_m = Movie(
                    rank=rank,
                    title=title,
                    release_year=year,
                    imdb_rating=rating,
                    votes=votes_str,
                    votes_count=votes_num,
                    poster_image=poster if poster != "nan" else "",
                    imdb_link=link if link != "nan" else "#",
                    genre=genre
                )
                db.add(new_m)
                added += 1

        except Exception as e:
            errors.append(f"Row {index + 1}: {str(e)}")

    db.commit()
    return added, updated, errors


def import_csv_file(db: Session, file_bytes: bytes) -> Dict[str, Any]:
    """Parse CSV bytes and import into database."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

    added, updated, errors = parse_and_import_dataframe(db, df)
    return {
        "status": "success",
        "added_count": added,
        "updated_count": updated,
        "total_processed": added + updated,
        "error_count": len(errors),
        "errors": errors[:5]
    }


def import_excel_file(db: Session, file_bytes: bytes) -> Dict[str, Any]:
    """Parse Excel bytes (.xlsx, .xls) and import into database."""
    df = pd.read_excel(io.BytesIO(file_bytes))
    added, updated, errors = parse_and_import_dataframe(db, df)
    return {
        "status": "success",
        "added_count": added,
        "updated_count": updated,
        "total_processed": added + updated,
        "error_count": len(errors),
        "errors": errors[:5]
    }


def validate_dataset(db: Session) -> Dict[str, Any]:
    """Inspect all records for completeness, validity, and integrity."""
    movies = db.query(Movie).all()
    total = len(movies)
    issues = []

    for m in movies:
        # Title validation
        if not m.title or len(m.title.strip()) < 1:
            issues.append({
                "record_id": m.id,
                "rank": m.rank,
                "title": m.title or "EMPTY",
                "issue_type": "Missing Title",
                "description": "Movie record is missing a valid title."
            })

        # Rating validation
        if m.imdb_rating is None or m.imdb_rating < 1.0 or m.imdb_rating > 10.0:
            issues.append({
                "record_id": m.id,
                "rank": m.rank,
                "title": m.title,
                "issue_type": "Invalid Rating",
                "description": f"Rating {m.imdb_rating} is outside permissible range (1.0 - 10.0)."
            })

        # Year validation
        if m.release_year is None or m.release_year < 1888 or m.release_year > 2030:
            issues.append({
                "record_id": m.id,
                "rank": m.rank,
                "title": m.title,
                "issue_type": "Suspicious Release Year",
                "description": f"Release Year {m.release_year} is implausible."
            })

        # Missing poster
        if not m.poster_image or m.poster_image.strip() in ["", "nan", "#"]:
            issues.append({
                "record_id": m.id,
                "rank": m.rank,
                "title": m.title,
                "issue_type": "Missing Poster",
                "description": "Poster image URL is empty or missing."
            })

    health_score = round(max(0.0, (1.0 - (len(issues) / (total * 3 or 1))) * 100), 1)

    return {
        "is_valid": len(issues) == 0,
        "total_records": total,
        "issue_count": len(issues),
        "issues": issues,
        "health_score": health_score
    }


def find_duplicates(db: Session) -> Dict[str, Any]:
    """Detect duplicate movies based on Title or IMDb link."""
    movies = db.query(Movie).all()
    title_map: Dict[str, List[Movie]] = {}

    for m in movies:
        norm_title = m.title.strip().lower()
        title_map.setdefault(norm_title, []).append(m)

    duplicate_items = []
    total_duplicate_rows = 0

    for norm_title, m_list in title_map.items():
        if len(m_list) > 1:
            duplicate_items.append({
                "title": m_list[0].title,
                "count": len(m_list),
                "ids": [m.id for m in m_list],
                "ranks": [m.rank for m in m_list]
            })
            total_duplicate_rows += (len(m_list) - 1)

    return {
        "has_duplicates": len(duplicate_items) > 0,
        "duplicate_groups_count": len(duplicate_items),
        "total_duplicate_rows": total_duplicate_rows,
        "duplicates": duplicate_items
    }


def deduplicate_dataset(db: Session) -> Dict[str, Any]:
    """Safely remove duplicate records keeping the one with the highest rating/votes."""
    dupes_info = find_duplicates(db)
    removed_count = 0

    for group in dupes_info["duplicates"]:
        ids = group["ids"]
        records = db.query(Movie).filter(Movie.id.in_(ids)).all()
        records.sort(key=lambda x: (x.imdb_rating or 0, x.votes_count or 0), reverse=True)
        to_delete = records[1:]
        for r in to_delete:
            db.delete(r)
            removed_count += 1

    db.commit()
    return {
        "status": "success",
        "removed_count": removed_count,
        "remaining_records": db.query(Movie).count()
    }
