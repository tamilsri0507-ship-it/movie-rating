from backend.routers.movies import router as movies_router
from backend.routers.recommendations import router as recommendations_router
from backend.routers.comparison import router as comparison_router
from backend.routers.analytics import router as analytics_router
from backend.routers.watchlist import router as watchlist_router
from backend.routers.scraper import router as scraper_router
from backend.routers.upload import router as upload_router
from backend.routers.dataset import router as dataset_router
from backend.routers.reports import router as reports_router

__all__ = [
    "movies_router",
    "recommendations_router",
    "comparison_router",
    "analytics_router",
    "watchlist_router",
    "scraper_router",
    "upload_router",
    "dataset_router",
    "reports_router",
]
