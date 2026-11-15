"""Comprehensive Automated Integration Test Suite for CineScope AI FastAPI Backend."""

import os
import sys
import io

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.services.movie_service import seed_initial_dataset

# Ensure test DB is clean with 250 records
db = SessionLocal()
seed_initial_dataset(db, force=True)
db.close()

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["framework"] == "FastAPI"
    print("[PASS] test_health_check")


def test_seed_and_list_movies():
    response = client.get("/api/movies")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total"] == 250, f"Expected 250 records in demo mode, got {data['total']}"
    assert len(data["movies"]) == 250
    first_movie = data["movies"][0]
    assert first_movie["Rank"] == 1
    assert "Shawshank" in first_movie["Title"]
    assert first_movie["IMDb Rating"] == 9.3
    print("[PASS] test_seed_and_list_movies (250 records verified)")


def test_search_and_filtering():
    # Filter by minimum rating
    r = client.get("/api/movies?min_rating=9.0")
    assert r.status_code == 200
    movies = r.json()["movies"]
    assert all(m["IMDb Rating"] >= 9.0 for m in movies)

    # Search keyword
    r = client.get("/api/movies?search=Godfather")
    assert r.status_code == 200
    assert any("Godfather" in m["Title"] for m in r.json()["movies"])

    # Filter decade
    r = client.get("/api/movies?decade=1990s")
    assert r.status_code == 200
    assert all(1990 <= m["Release Year"] <= 1999 for m in r.json()["movies"])
    print("[PASS] test_search_and_filtering")


def test_analytics_endpoints():
    # 1. Summary stats
    r = client.get("/api/stats")
    assert r.status_code == 200
    stats = r.json()["stats"]
    assert stats["total_movies"] == 250
    assert stats["avg_rating"] > 8.0
    assert stats["top_movie"] == "The Shawshank Redemption"
    assert stats["top_rating"] == 9.3

    # 2. Decades
    r = client.get("/api/analytics/decades")
    assert r.status_code == 200
    assert len(r.json()["decades"]) >= 8

    # 3. Genres
    r = client.get("/api/analytics/genres")
    assert r.status_code == 200
    assert len(r.json()["genres"]) >= 5

    # 4. Ratings
    r = client.get("/api/analytics/ratings")
    assert r.status_code == 200
    data = r.json()
    assert data["mean_rating"] > 8.0
    assert len(data["rating_bins"]) == 4
    print("[PASS] test_analytics_endpoints (Summary, Decades, Genres, Ratings)")


def test_movie_crud():
    # 1. Create
    new_movie = {
        "rank": 999,
        "title": "CineScope Test Film",
        "release_year": 2024,
        "imdb_rating": 8.7,
        "votes": "50,000",
        "votes_count": 50000,
        "poster_image": "https://placehold.co/380x560",
        "imdb_link": "https://www.imdb.com/title/tt9999999/",
        "genre": "Sci-Fi, Drama"
    }
    r = client.post("/api/movies", json=new_movie)
    assert r.status_code == 201
    created = r.json()["movie"]
    movie_id = created["id"]
    assert created["Title"] == "CineScope Test Film"

    # 2. Read
    r = client.get(f"/api/movies/{movie_id}")
    assert r.status_code == 200
    assert r.json()["movie"]["id"] == movie_id

    # 3. Update
    r = client.put(f"/api/movies/{movie_id}", json={"imdb_rating": 8.9, "votes": "60,000"})
    assert r.status_code == 200
    assert r.json()["movie"]["IMDb Rating"] == 8.9

    # 4. Delete
    r = client.delete(f"/api/movies/{movie_id}")
    assert r.status_code == 200

    # Verify 404 after delete
    r = client.get(f"/api/movies/{movie_id}")
    assert r.status_code == 404
    print("[PASS] test_movie_crud (Create, Read, Update, Delete)")


def test_ai_recommendations():
    # Recommend similar to #1 (Shawshank Redemption - Drama)
    r = client.get("/api/recommendations/1?limit=4")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["algorithm"] == "Scikit-Learn TF-IDF Vectorizer + Cosine Similarity"
    assert len(data["recommendations"]) == 4
    for rec in data["recommendations"]:
        assert rec["similarity_score"] > 0
        assert "%" in rec["match_percentage"]
        assert len(rec["explanation"]) > 0
    print("[PASS] test_ai_recommendations (TF-IDF + Cosine Similarity)")


def test_movie_comparison():
    # Compare #1 (Shawshank) vs #3 (The Dark Knight)
    r = client.get("/api/movies/compare?movie1_id=1&movie2_id=3")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "verdict" in data
    assert data["rating_diff"] >= 0
    assert "similarity_percentage" in data
    assert len(data["metrics_table"]) >= 5
    print("[PASS] test_movie_comparison (Side-by-side head-to-head metrics)")


def test_watchlist_workflow():
    # Add movie #2 to watchlist
    r = client.post("/api/watchlist/2", json={"notes": "Must watch with friends", "priority": "High"})
    assert r.status_code == 201

    # Check
    r = client.get("/api/watchlist/check/2")
    assert r.status_code == 200
    assert r.json()["is_in_watchlist"] is True

    # List
    r = client.get("/api/watchlist")
    assert r.status_code == 200
    items = r.json()["watchlist"]
    assert any(item["movie_id"] == 2 for item in items)

    # Remove
    r = client.delete("/api/watchlist/2")
    assert r.status_code == 200

    # Verify check is false
    r = client.get("/api/watchlist/check/2")
    assert r.json()["is_in_watchlist"] is False
    print("[PASS] test_watchlist_workflow (Add, Check, List, Remove)")


def test_dataset_quality_and_duplicates():
    r = client.get("/api/dataset/validate")
    assert r.status_code == 200
    data = r.json()
    assert data["total_records"] == 250
    assert data["health_score"] >= 90.0

    r = client.get("/api/dataset/duplicates")
    assert r.status_code == 200
    assert "has_duplicates" in r.json()
    print("[PASS] test_dataset_quality_and_duplicates (Health Score & Duplicate Check)")


def test_pdf_report_generation():
    r = client.get("/api/reports/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 2000
    assert r.content.startswith(b"%PDF")
    print("[PASS] test_pdf_report_generation (ReportLab Lavender PDF generated)")


def test_exports_and_imports():
    # 1. Download CSV
    r = client.get("/api/download/csv")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    csv_bytes = r.content
    assert b"The Shawshank Redemption" in csv_bytes

    # 2. Upload CSV
    upload_file = io.BytesIO(csv_bytes)
    r = client.post(
        "/api/upload/csv",
        files={"file": ("test_import.csv", upload_file, "text/csv")}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    # 3. Download Excel
    r = client.get("/api/download/excel")
    assert r.status_code == 200
    assert "spreadsheet" in r.headers["content-type"]
    excel_bytes = r.content

    # 4. Upload Excel
    excel_file = io.BytesIO(excel_bytes)
    r = client.post(
        "/api/upload/excel",
        files={"file": ("test_import.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    print("[PASS] test_exports_and_imports (CSV & Excel download/upload verified)")


def test_frontend_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "CineScope" in r.text
    assert "/static/style.css" in r.text
    assert "/static/script.js" in r.text
    print("[PASS] test_frontend_html (Light Lavender Dashboard UI 200 OK)")


if __name__ == "__main__":
    test_health_check()
    test_frontend_html()
    test_seed_and_list_movies()
    test_search_and_filtering()
    test_analytics_endpoints()
    test_movie_crud()
    test_ai_recommendations()
    test_movie_comparison()
    test_watchlist_workflow()
    test_dataset_quality_and_duplicates()
    test_pdf_report_generation()
    test_exports_and_imports()
    print("=" * 60)
    print("  ALL 11 BACKEND TEST SUITES COMPLETED AND PASSED 100%!  ")
    print("=" * 60)
