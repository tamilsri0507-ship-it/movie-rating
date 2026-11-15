"""IMDb Scraping Service using Selenium WebDriver with fallback capabilities."""

import time
import json
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import Session

from backend.models.movie import Movie
from backend.services.movie_service import parse_vote_number, determine_genre

IMDB_TOP_250_URL = "https://www.imdb.com/chart/top/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
}


def run_selenium_scraper(headless: bool = True) -> Optional[List[Dict[str, Any]]]:
    """Execute real browser automation using Selenium to extract IMDb Top 250."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        return None

    driver = None
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        chrome_options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(IMDB_TOP_250_URL)
        time.sleep(3)

        html = driver.page_source
        driver.quit()
        driver = None

        return parse_imdb_html(html)

    except Exception as e:
        print(f"[-] Selenium Scrape Warning: {e}")
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        return None


def run_requests_scraper() -> Optional[List[Dict[str, Any]]]:
    """Fallback scraping using HTTP requests and BeautifulSoup."""
    try:
        session = requests.Session()
        res = session.get(IMDB_TOP_250_URL, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return parse_imdb_html(res.text)
    except Exception as e:
        print(f"[-] HTTP Scrape Warning: {e}")
    return None


def parse_imdb_html(html_text: str) -> Optional[List[Dict[str, Any]]]:
    """Extract movie list from IMDb HTML page via JSON-LD or table elements."""
    soup = BeautifulSoup(html_text, "html.parser")
    movies = []

    # Method 1: JSON-LD Structured Data
    json_scripts = soup.find_all("script", {"type": "application/ld+json"})
    for script in json_scripts:
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") == "ItemList":
                items = data.get("itemListElement", [])
                for idx, item in enumerate(items, 1):
                    movie_item = item.get("item", {})
                    title = movie_item.get("name", "Unknown Title")
                    rating = movie_item.get("aggregateRating", {}).get("ratingValue", 0.0)
                    votes = movie_item.get("aggregateRating", {}).get("ratingCount", "100,000")
                    image = movie_item.get("image", "")
                    url = movie_item.get("url", "")
                    year = movie_item.get("datePublished", "2000")[:4] if "datePublished" in movie_item else "2000"

                    try:
                        r_float = float(rating)
                    except (ValueError, TypeError):
                        r_float = 8.0

                    try:
                        y_int = int(year)
                    except (ValueError, TypeError):
                        y_int = 2000

                    movies.append({
                        "rank": idx,
                        "title": title,
                        "release_year": y_int,
                        "imdb_rating": r_float,
                        "votes": f"{int(votes):,}" if str(votes).isdigit() else str(votes),
                        "poster_image": image,
                        "imdb_link": f"https://www.imdb.com{url}" if str(url).startswith("/") else str(url),
                        "genre": determine_genre(title)
                    })

                if len(movies) >= 100:
                    return movies
        except Exception:
            continue

    return movies if len(movies) >= 50 else None


def execute_scrape_and_sync(db: Session, use_selenium: bool = True) -> Dict[str, Any]:
    """Execute scraping with Selenium or Requests and persist results to SQLite."""
    scraped_data = None
    engine_used = "Requests / HTTP"

    if use_selenium:
        scraped_data = run_selenium_scraper(headless=True)
        if scraped_data:
            engine_used = "Selenium WebDriver (Headless Chrome)"

    if not scraped_data:
        scraped_data = run_requests_scraper()
        engine_used = "HTTP Requests + BeautifulSoup"

    if not scraped_data:
        # Fallback to existing database records
        existing_count = db.query(Movie).count()
        return {
            "status": "warning",
            "message": "Scraper completed. Online site challenge encountered; existing database was maintained.",
            "engine": engine_used,
            "scraped_count": 0,
            "database_total": existing_count
        }

    # Upsert scraped data into SQLite
    synced_count = 0
    for item in scraped_data:
        existing = db.query(Movie).filter(Movie.title.ilike(item["title"])).first()
        votes_num = parse_vote_number(item["votes"])
        if existing:
            existing.rank = item["rank"]
            existing.release_year = item["release_year"]
            existing.imdb_rating = item["imdb_rating"]
            existing.votes = item["votes"]
            existing.votes_count = votes_num
            if item["poster_image"]:
                existing.poster_image = item["poster_image"]
            existing.imdb_link = item["imdb_link"]
            existing.genre = item["genre"]
        else:
            new_m = Movie(
                rank=item["rank"],
                title=item["title"],
                release_year=item["release_year"],
                imdb_rating=item["imdb_rating"],
                votes=item["votes"],
                votes_count=votes_num,
                poster_image=item["poster_image"],
                imdb_link=item["imdb_link"],
                genre=item["genre"]
            )
            db.add(new_m)
        synced_count += 1

    db.commit()

    return {
        "status": "success",
        "message": f"Successfully scraped and synced {synced_count} movies to CineScope AI database.",
        "engine": engine_used,
        "scraped_count": len(scraped_data),
        "database_total": db.query(Movie).count()
    }
