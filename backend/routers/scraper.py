"""IMDb Live Scraping Router using Selenium WebDriver."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.scraper_service import execute_scrape_and_sync
from backend.models.movie import Movie

router = APIRouter(prefix="/api/scrape", tags=["IMDb Scraper"])


class ScrapeRequest(BaseModel):
    use_selenium: Optional[bool] = True
    headless: Optional[bool] = True


@router.post("", summary="Trigger live IMDb Top 250 scraping using Selenium")
def trigger_scrape(payload: Optional[ScrapeRequest] = None, db: Session = Depends(get_db)):
    """
    Automates Chrome browser extraction of IMDb Top 250 chart.
    Parses live data, extracts ratings and posters, and syncs directly into SQLite.
    """
    use_selenium = payload.use_selenium if payload is not None else True
    res = execute_scrape_and_sync(db, use_selenium=use_selenium)

    sample_movies = db.query(Movie).order_by(Movie.rank.asc()).limit(20).all()
    return {
        **res,
        "count": res.get("scraped_count", 0),
        "movies": [m.to_dict() for m in sample_movies]
    }
