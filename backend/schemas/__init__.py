from backend.schemas.movie import MovieBase, MovieCreate, MovieUpdate, MovieResponse, MovieListResponse
from backend.schemas.analytics import SummaryStats, RatingAnalyticsResponse, GenreAnalyticsResponse, DecadeAnalyticsResponse
from backend.schemas.recommendation import RecommendationResponse, RecommendedMovieItem
from backend.schemas.comparison import MovieComparisonResponse
from backend.schemas.watchlist import WatchlistCreate, WatchlistResponse, WatchlistCheckResponse
from backend.schemas.dataset import DatasetValidationResponse, DatasetDuplicatesResponse

__all__ = [
    "MovieBase", "MovieCreate", "MovieUpdate", "MovieResponse", "MovieListResponse",
    "SummaryStats", "RatingAnalyticsResponse", "GenreAnalyticsResponse", "DecadeAnalyticsResponse",
    "RecommendationResponse", "RecommendedMovieItem",
    "MovieComparisonResponse",
    "WatchlistCreate", "WatchlistResponse", "WatchlistCheckResponse",
    "DatasetValidationResponse", "DatasetDuplicatesResponse"
]
