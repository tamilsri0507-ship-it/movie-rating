from backend.services.movie_service import (
    seed_initial_dataset,
    get_all_movies,
    get_movie_by_id,
    create_movie,
    update_movie,
    delete_movie
)
from backend.services.ai_recommender import ai_recommender
from backend.services.analytics_service import (
    compute_summary_stats,
    compute_decade_distribution,
    compute_genre_distribution,
    compute_rating_analytics
)
from backend.services.comparison_service import compare_two_movies
from backend.services.watchlist_service import (
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    is_in_watchlist
)
from backend.services.file_service import (
    import_csv_file,
    import_excel_file,
    validate_dataset,
    find_duplicates,
    deduplicate_dataset
)
from backend.services.scraper_service import execute_scrape_and_sync
from backend.services.pdf_service import generate_cinescope_pdf

__all__ = [
    "seed_initial_dataset", "get_all_movies", "get_movie_by_id", "create_movie", "update_movie", "delete_movie",
    "ai_recommender",
    "compute_summary_stats", "compute_decade_distribution", "compute_genre_distribution", "compute_rating_analytics",
    "compare_two_movies",
    "get_watchlist", "add_to_watchlist", "remove_from_watchlist", "is_in_watchlist",
    "import_csv_file", "import_excel_file", "validate_dataset", "find_duplicates", "deduplicate_dataset",
    "execute_scrape_and_sync",
    "generate_cinescope_pdf"
]
