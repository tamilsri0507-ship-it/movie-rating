"""CineScope AI FastAPI Application Main Entrypoint."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base, SessionLocal
from backend.services.movie_service import seed_initial_dataset
from backend.routers import (
    comparison_router,
    movies_router,
    recommendations_router,
    analytics_router,
    watchlist_router,
    scraper_router,
    upload_router,
    dataset_router,
    reports_router,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event to initialize tables and seed exactly 250 records in demo mode."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = seed_initial_dataset(db, force=False)
        print(f"[+] CineScope AI SQLite Database initialized with {count} records in demo mode.")
    finally:
        db.close()

    yield
    print("[-] Shutting down CineScope AI server.")


app = FastAPI(
    title="CineScope AI - REST API Documentation",
    description="""
# CineScope AI Movie Tracker & Analytics Backend

Welcome to the CineScope AI API documentation. Built with **FastAPI**, **SQLite**, **SQLAlchemy**, **Pandas**, **Scikit-learn**, and **Selenium**.

### Key Modules:
- **Movies**: Full CRUD, live multi-field filtering, decade search, and sorting.
- **AI Recommendations**: Scikit-Learn TF-IDF Vectorization & Cosine Similarity matches.
- **Movie Comparison**: Head-to-head metric comparison and content similarity indexes.
- **Analytics & Graphs**: Decade distribution, genre market share, and rating histograms.
- **Watchlist**: Personal bookmarking with notes and priority tags.
- **Web Scraper**: Real-time browser automation using Selenium.
- **Upload & Export**: CSV and Excel (.xlsx) data ingestion, plus ReportLab PDF report generation.
- **Dataset Quality**: Integrity validation, health scoring, and duplicate removal.
    """,
    version="2.4.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for local frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Static Files & Templates
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else None


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend(request: Request):
    """Serve the CineScope AI Light Lavender Frontend Dashboard."""
    if templates and os.path.exists(os.path.join(TEMPLATES_DIR, "index.html")):
        return templates.TemplateResponse(request=request, name="index.html")
    return HTMLResponse("<h1>CineScope AI Backend Running. Visit <a href='/docs'>/docs</a> for Swagger UI.</h1>")


@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "service": "CineScope AI Backend",
        "framework": "FastAPI",
        "database": "SQLite (cinescope.db)",
        "theme": "Light Lavender & Soft Purple (#F7F3FF / #7952B3)",
        "docs": "/docs"
    }


# Register All API Routers (comparison before movies to resolve route precedence)
app.include_router(comparison_router)
app.include_router(movies_router)
app.include_router(recommendations_router)
app.include_router(analytics_router)
app.include_router(watchlist_router)
app.include_router(scraper_router)
app.include_router(upload_router)
app.include_router(dataset_router)
app.include_router(reports_router)

if __name__ == "__main__":
    import uvicorn
    print("[+] Launching CineScope AI FastAPI Server on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
