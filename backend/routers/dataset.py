"""Dataset Quality, Validation, and Duplicate Detection Router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.file_service import (
    validate_dataset,
    find_duplicates,
    deduplicate_dataset
)

router = APIRouter(prefix="/api/dataset", tags=["Dataset Validation & Quality"])


@router.get("/validate", summary="Validate dataset health and identify missing or malformed fields")
def get_dataset_validation(db: Session = Depends(get_db)):
    """
    Scans all movie records in SQLite database.
    Checks for: missing titles, out-of-range ratings, suspicious release years, and missing posters.
    Calculates overall data health score.
    """
    res = validate_dataset(db)
    return {"status": "success", **res}


@router.get("/duplicates", summary="Detect duplicate movie records")
def get_dataset_duplicates(db: Session = Depends(get_db)):
    """Find duplicate movies in the collection grouped by normalized title."""
    res = find_duplicates(db)
    return {"status": "success", **res}


@router.post("/deduplicate", summary="Clean up duplicate records")
def deduplicate_movies(db: Session = Depends(get_db)):
    """Automatically keep the best record for each movie and purge duplicates."""
    res = deduplicate_dataset(db)
    return res
