# 🎬 CineScope AI - Light Lavender & Soft Purple Movie Intelligence Dashboard

A full-stack movie intelligence platform built with **FastAPI**, **SQLite**, **SQLAlchemy**, **Scikit-learn**, **Pandas**, **Selenium**, and a responsive frontend featuring a Light Lavender and Soft Purple design system.

---

## 🎨 Theme & Color Palette

Designed according to strict specifications:
- **Main Background**: `#F7F3FF`
- **Primary Accent**: `#B99AFF`
- **Light Lavender**: `#E6D9FF` (Sidebar, Badges, Subtle highlights)
- **Cards**: `#FFFFFF` (White cards with soft lavender drop-shadows)
- **Buttons**: `#7952B3` (Soft purple gradient buttons)
- **Text**: `#29213A` (Crisp, high-contrast dark purple/slate)
- **Borders**: `#E8DDF8` (Soft lavender boundary lines)

---

## 🚀 Key Features

1. **Exact 250 Movies in Demo Mode**:
   - Seeded from `imdb_top_250.csv` into local SQLite database (`cinescope.db`).
   - Genuine records, ratings, vote counts, genres, release years, and poster URLs.

2. **Full REST API Suite (FastAPI + Pydantic v2)**:
   - Full CRUD: Create, Read, Update, Delete (`/api/movies`).
   - Advanced Search, Decade/Genre/Rating Filtering, and Multi-column Sorting.
   - Interactive Swagger UI documentation at [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs).

3. **AI Recommendations Engine (TF-IDF & Cosine Similarity)**:
   - Computes genuine content similarity matrices using scikit-learn.
   - Features match percentage, shared genre DNA, era alignment, and explanation tags (`/api/recommendations/{id}`).

4. **Head-to-Head Movie Comparison**:
   - Compares rating difference, release gap, vote disparity, shared genres, and cosine similarity (`/api/movies/compare`).

5. **Personal Watchlist**:
   - User movie bookmarks with persistence in SQLite (`/api/watchlist`).
   - Live heart bookmark toggling on cards and table rows with reactive tab switching.

6. **Interactive Analytics & Chart Switcher**:
   - Switchable Chart.js visualizer between Decades, Genres, and Rating caliber tiers (`/api/analytics/decades`, `/api/analytics/genres`, `/api/analytics/ratings`).

7. **Automated IMDb Scraping (Selenium)**:
   - Headless Selenium WebDriver with robust JSON-LD/HTTP fallback synchronization (`/api/scrape`).

8. **Dataset Integrity & Duplicate Detection**:
   - Dataset health validation and duplicate record detection/purge (`/api/dataset/validate`, `/api/dataset/duplicates`, `/api/dataset/deduplicate`).

9. **CSV & Excel Import / Export**:
   - Drag-and-drop file ingestion supporting `.csv`, `.xlsx`, and `.xls` (`/api/upload/csv`, `/api/upload/excel`).
   - Instant export downloads (`/api/download/csv`, `/api/download/excel`).

10. **Lavender PDF Intelligence Report Generation**:
    - ReportLab PDF engine compiling KPI summary cards, era breakdown, genre breakdown, and top ranked films in the theme palette (`/api/reports/pdf`).

---

## 💻 Windows PowerShell Run Commands

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Backend Integration Test Suite
```powershell
python tests/test_backend.py
```
*(Runs 11 test suites covering all endpoints, database seeding, AI recommendations, comparison, scraper, uploads, and PDF generation).*

### 3. Start the FastAPI Server
```powershell
python run.py
```
*Or via Uvicorn directly:*
```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Access URLs
- **Web Application Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger UI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📁 Project Architecture

```
movie tracker/
├── backend/
│   ├── database.py              # SQLite engine, SessionLocal, Base & get_db dependency
│   ├── main.py                  # FastAPI app, CORS, routes & lifespan seeding
│   ├── models/
│   │   ├── movie.py             # SQLAlchemy Movie model (rank, title, genre, rating...)
│   │   └── watchlist.py         # SQLAlchemy WatchlistItem model with relationships
│   ├── schemas/
│   │   ├── movie.py             # Pydantic Movie schemas with validators
│   │   ├── analytics.py         # Summary, decade, genre & rating schemas
│   │   ├── recommendation.py    # TF-IDF similarity response schema
│   │   ├── comparison.py        # Side-by-side comparison schema
│   │   ├── watchlist.py         # Watchlist schema
│   │   └── dataset.py           # Dataset validation & duplicate detection schema
│   ├── services/
│   │   ├── movie_service.py     # CRUD, filtering, pagination & database seeding
│   │   ├── ai_recommender.py    # Scikit-learn TF-IDF + Cosine Similarity engine
│   │   ├── analytics_service.py # Decades, genres, and rating statistics
│   │   ├── comparison_service.py# Head-to-head metrics & AI similarity calculation
│   │   ├── watchlist_service.py # Watchlist database operations
│   │   ├── file_service.py      # CSV/Excel parsing, validation & deduplication
│   │   ├── scraper_service.py   # Selenium scraper with HTTP fallback
│   │   └── pdf_service.py       # ReportLab PDF generation in lavender palette
│   └── routers/
│       ├── movies.py            # /api/movies (CRUD, search, filter, sort)
│       ├── recommendations.py   # /api/recommendations/{id}
│       ├── comparison.py        # /api/movies/compare & /api/compare
│       ├── analytics.py         # /api/stats, /api/analytics/...
│       ├── watchlist.py         # /api/watchlist
│       ├── scraper.py           # /api/scrape
│       ├── upload.py            # /api/upload/csv, /api/upload/excel, /api/download/...
│       ├── dataset.py           # /api/dataset/validate, /duplicates, /deduplicate
│       └── reports.py           # /api/reports/pdf
├── static/
│   ├── style.css                # Light Lavender & Soft Purple styling
│   └── script.js                # Frontend REST API integration & UI controls
├── templates/
│   └── index.html               # Responsive HTML5 layout with sidebar & modals
├── tests/
│   └── test_backend.py          # 11 integration test suites (100% passing)
├── cinescope.db                 # SQLite database (seeded with 250 movies)
├── imdb_top_250.csv             # Raw IMDb dataset
├── requirements.txt             # Project dependencies
└── run.py                       # Server runner
```
