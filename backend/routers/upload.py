"""CSV and Excel Upload & Export Router."""

import io
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.movie import Movie
from backend.services.file_service import import_csv_file, import_excel_file
from backend.services.movie_service import get_all_movies

router = APIRouter(tags=["File Upload & Export"])


def format_movies_dataframe(movies):
    """Format movie records into a clean, presentation-ready DataFrame."""
    rows = []
    for m in movies:
        rows.append({
            "Rank": int(m.rank),
            "Title": str(m.title),
            "Release Year": int(m.release_year),
            "IMDb Rating": float(m.imdb_rating),
            "Votes": str(m.votes),
            "Poster Image": str(m.poster_image or ""),
            "IMDb Link": str(m.imdb_link or "#"),
            "Genre": str(m.genre or "Drama")
        })
    df = pd.DataFrame(rows)
    df["IMDb Rating"] = df["IMDb Rating"].astype(float)
    return df


@router.post("/api/upload/csv", summary="Upload custom movie CSV file")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload, parse, validate and import a CSV file into SQLite database."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .csv files are supported."
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    res = import_csv_file(db, contents)
    movies, _ = get_all_movies(db, limit=250)
    return {
        "status": "success",
        "message": f"Successfully processed CSV. Added {res['added_count']} new and updated {res['updated_count']} movies.",
        "count": len(movies),
        "movies": [m.to_dict() for m in movies],
        **res
    }


@router.post("/api/upload-csv", summary="Upload CSV (legacy form compatibility)")
async def upload_csv_legacy(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Legacy endpoint alias for index.html upload form."""
    return await upload_csv(file=file, db=db)


@router.post("/api/upload/excel", summary="Upload custom movie Excel file (.xlsx, .xls)")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload, parse, validate and import an Excel spreadsheet into SQLite."""
    fn = file.filename.lower()
    if not (fn.endswith(".xlsx") or fn.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .xlsx and .xls Excel files are supported."
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded Excel file is empty.")

    res = import_excel_file(db, contents)
    movies, _ = get_all_movies(db, limit=250)
    return {
        "status": "success",
        "message": f"Successfully processed Excel spreadsheet. Added {res['added_count']} new and updated {res['updated_count']} movies.",
        "count": len(movies),
        "movies": [m.to_dict() for m in movies],
        **res
    }


@router.get("/api/download/csv", summary="Export database movies to CSV")
def download_csv(db: Session = Depends(get_db)):
    """Generate and download a clean CSV file of all movies currently in SQLite database."""
    movies = db.query(Movie).order_by(Movie.rank.asc()).all()
    df = format_movies_dataframe(movies)

    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8")
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cinescope_movies.csv"}
    )


@router.get("/api/download-csv", summary="Download CSV (legacy link compatibility)")
def download_csv_legacy(db: Session = Depends(get_db)):
    return download_csv(db=db)


@router.get("/api/download/excel", summary="Export database movies to Excel (.xlsx)")
def download_excel(db: Session = Depends(get_db)):
    """Generate and download an Excel spreadsheet of all movies."""
    movies = db.query(Movie).order_by(Movie.rank.asc()).all()
    df = format_movies_dataframe(movies)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="CineScope Movies")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cinescope_movies.xlsx"}
    )
