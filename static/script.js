// ==========================================================================
// CineScope AI - Light Lavender & Soft Purple Movie Intelligence Dashboard
// Full REST API Integration with FastAPI & SQLite
// ==========================================================================

let allMovies = [];
let filteredMovies = [];
let watchlistMovieIds = new Set();
let currentView = 'grid'; // 'grid' or 'table'
let currentMode = 'all';  // 'all' or 'watchlist'
let currentChartType = 'decade'; // 'decade', 'genre', or 'rating'
let chartInstance = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

// App Initialization
async function initApp() {
    await fetchWatchlist();
    await fetchMovies();
    await fetchStats();
    populateComparisonSelects();
}

// ==========================================================================
// API Calls: Movies, Stats, and Watchlist
// ==========================================================================

// Fetch movies from FastAPI /api/movies endpoint
async function fetchMovies() {
    try {
        const response = await fetch("/api/movies?limit=250");
        const data = await response.json();
        if (data.status === "success" && Array.isArray(data.movies)) {
            allMovies = data.movies;
            applyFilters();
            populateComparisonSelects();
        } else {
            showToast("Failed to parse movie data from server.", "error");
        }
    } catch (err) {
        console.error("fetchMovies error:", err);
        showToast("Error connecting to FastAPI backend.", "error");
    }
}

// Fetch dashboard statistics
async function fetchStats() {
    try {
        const response = await fetch("/api/stats");
        const data = await response.json();
        if (data.status === "success" && data.stats) {
            const stats = data.stats;
            const totalEl = document.getElementById("statTotalMovies");
            const topMovieEl = document.getElementById("statTopMovie");
            const avgRatingEl = document.getElementById("statAvgRating");
            const topDecadeEl = document.getElementById("statTopDecade");

            if (totalEl) totalEl.textContent = stats.total_movies;
            if (topMovieEl) topMovieEl.textContent = stats.top_movie;
            if (avgRatingEl) avgRatingEl.textContent = typeof stats.avg_rating === 'number' ? stats.avg_rating.toFixed(1) : stats.avg_rating;
            if (topDecadeEl) topDecadeEl.textContent = stats.top_decade || "1990s";

            // Render active chart
            loadChartData(currentChartType, stats.decades);
        }
    } catch (err) {
        console.error("fetchStats error:", err);
    }
}

// Fetch user watchlist bookmarks
async function fetchWatchlist() {
    try {
        const response = await fetch("/api/watchlist");
        const data = await response.json();
        if (data.status === "success" && Array.isArray(data.watchlist)) {
            watchlistMovieIds.clear();
            data.watchlist.forEach(item => {
                if (item.movie_id) watchlistMovieIds.add(item.movie_id);
            });
            updateWatchlistBadges();
        }
    } catch (err) {
        console.error("fetchWatchlist error:", err);
    }
}

// Update watchlist badge counts in sidebar and toolbar
function updateWatchlistBadges() {
    const count = watchlistMovieIds.size;
    const sidebarCount = document.getElementById("sidebarWatchlistCount");
    const toolbarCount = document.getElementById("watchlistBadgeCount");
    if (sidebarCount) sidebarCount.textContent = count;
    if (toolbarCount) toolbarCount.textContent = count;
}

// Toggle movie in/out of watchlist
async function toggleWatchlist(movieId) {
    if (!movieId) return;
    const isBookmarked = watchlistMovieIds.has(movieId);

    try {
        if (isBookmarked) {
            // Delete from watchlist
            const res = await fetch(`/api/watchlist/${movieId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.status === "success") {
                watchlistMovieIds.delete(movieId);
                updateWatchlistBadges();
                showToast("Removed movie from your watchlist.", "success");
            }
        } else {
            // Add to watchlist
            const res = await fetch(`/api/watchlist/${movieId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ notes: "Added via CineScope AI", priority: "Normal" })
            });
            const data = await res.json();
            if (data.status === "success") {
                watchlistMovieIds.add(movieId);
                updateWatchlistBadges();
                showToast("Added movie to your watchlist!", "success");
            }
        }

        // Re-render to reflect bookmark state change
        if (currentMode === 'watchlist') {
            applyFilters();
        } else {
            renderMovies();
        }
    } catch (err) {
        console.error("toggleWatchlist error:", err);
        showToast("Failed to update watchlist.", "error");
    }
}

// ==========================================================================
// Chart.js Switcher: Decades, Genres, and Ratings
// ==========================================================================

async function switchChartType(type) {
    currentChartType = type;

    // Toggle button active classes
    const decadeBtn = document.getElementById("chartDecadeBtn");
    const genreBtn = document.getElementById("chartGenreBtn");
    const ratingBtn = document.getElementById("chartRatingBtn");

    if (decadeBtn) decadeBtn.classList.toggle("active", type === 'decade');
    if (genreBtn) genreBtn.classList.toggle("active", type === 'genre');
    if (ratingBtn) ratingBtn.classList.toggle("active", type === 'rating');

    const mainTitle = document.getElementById("chartMainTitle");
    const subTitle = document.getElementById("chartSubTitle");

    if (type === 'decade') {
        if (mainTitle) mainTitle.innerHTML = `<i class="fa-solid fa-chart-bar"></i> Movie Distribution by Decade`;
        if (subTitle) subTitle.textContent = "IMDb Top Rankings Breakdown & Era Concentration";
        await loadChartData('decade');
    } else if (type === 'genre') {
        if (mainTitle) mainTitle.innerHTML = `<i class="fa-solid fa-shapes"></i> Movie Distribution by Genre`;
        if (subTitle) subTitle.textContent = "Genre Frequency & Market Concentration Across Top 250";
        await loadChartData('genre');
    } else if (type === 'rating') {
        if (mainTitle) mainTitle.innerHTML = `<i class="fa-solid fa-star-half-stroke"></i> Rating Caliber Distribution`;
        if (subTitle) subTitle.textContent = "Distribution of IMDb Scores across Masterpiece, Acclaimed, and Classic Tiers";
        await loadChartData('rating');
    }
}

async function loadChartData(type, preloadedDecades = null) {
    const canvas = document.getElementById("decadeChart");
    if (!canvas) return;

    if (type === 'decade') {
        if (preloadedDecades) {
            renderBarChart(Object.keys(preloadedDecades), Object.values(preloadedDecades), "Movies Count", "Top Movies");
        } else {
            try {
                const res = await fetch("/api/analytics/decades");
                const data = await res.json();
                if (data.status === "success" && Array.isArray(data.decades)) {
                    const labels = data.decades.map(d => d.decade);
                    const counts = data.decades.map(d => d.count);
                    renderBarChart(labels, counts, "Movies Count", "Top Movies");
                }
            } catch (err) {
                console.error("Decade chart error:", err);
            }
        }
    } else if (type === 'genre') {
        try {
            const res = await fetch("/api/analytics/genres");
            const data = await res.json();
            if (data.status === "success" && Array.isArray(data.genres)) {
                // Top 10 genres
                const topGenres = data.genres.slice(0, 10);
                const labels = topGenres.map(g => g.genre);
                const counts = topGenres.map(g => g.count);
                renderBarChart(labels, counts, "Films in Genre", "Movies");
            }
        } catch (err) {
            console.error("Genre chart error:", err);
        }
    } else if (type === 'rating') {
        try {
            const res = await fetch("/api/analytics/ratings");
            const data = await res.json();
            if (data.status === "success" && Array.isArray(data.rating_bins)) {
                const labels = data.rating_bins.map(b => b.label);
                const counts = data.rating_bins.map(b => b.count);
                renderBarChart(labels, counts, "Number of Films", "Films");
            }
        } catch (err) {
            console.error("Rating chart error:", err);
        }
    }
}

// Render generic purple gradient bar chart
function renderBarChart(labels, counts, datasetLabel, tooltipSuffix) {
    const canvas = document.getElementById("decadeChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const chartHeight = canvas.parentElement ? canvas.parentElement.clientHeight : 260;
    const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight || 260);
    gradient.addColorStop(0, "rgba(185, 154, 255, 0.95)");  // Primary: #B99AFF
    gradient.addColorStop(0.5, "rgba(142, 98, 205, 0.85)");
    gradient.addColorStop(1, "rgba(121, 82, 179, 0.70)");   // Button: #7952B3

    const hoverGradient = ctx.createLinearGradient(0, 0, 0, chartHeight || 260);
    hoverGradient.addColorStop(0, "rgba(121, 82, 179, 1)");
    hoverGradient.addColorStop(1, "rgba(104, 65, 161, 0.9)");

    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: datasetLabel,
                data: counts,
                backgroundColor: gradient,
                hoverBackgroundColor: hoverGradient,
                borderColor: "#7952B3",
                borderWidth: 1.5,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 600,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#FFFFFF",
                    titleColor: "#7952B3",
                    titleFont: { family: "'Outfit', sans-serif", size: 13, weight: "700" },
                    bodyColor: "#29213A",
                    bodyFont: { family: "'Outfit', sans-serif", size: 12, weight: "600" },
                    borderColor: "#E8DDF8",
                    borderWidth: 1.5,
                    padding: 12,
                    cornerRadius: 10,
                    boxPadding: 6,
                    usePointStyle: true,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y} ${tooltipSuffix}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: "rgba(232, 221, 248, 0.6)",
                        drawBorder: false
                    },
                    ticks: {
                        color: "#5C4F75",
                        font: { family: "'Outfit', sans-serif", size: 11, weight: "600" }
                    }
                },
                y: {
                    grid: {
                        color: "rgba(232, 221, 248, 0.6)",
                        drawBorder: false
                    },
                    ticks: {
                        color: "#5C4F75",
                        font: { family: "'Outfit', sans-serif", size: 12, weight: "600" },
                        precision: 0
                    }
                }
            }
        }
    });
}

// ==========================================================================
// Filtering, Searching, and Sorting
// ==========================================================================

function applyFilters() {
    const searchInput = document.getElementById("searchInput");
    const genreFilter = document.getElementById("genreFilter");
    const ratingFilter = document.getElementById("ratingFilter");
    const sortBy = document.getElementById("sortBy");

    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const selectedGenre = genreFilter ? genreFilter.value : "All";
    const minRating = ratingFilter ? (parseFloat(ratingFilter.value) || 0) : 0;
    const sortVal = sortBy ? sortBy.value : "rank-asc";

    filteredMovies = allMovies.filter(movie => {
        const title = (movie.Title || movie.title || "").toLowerCase();
        const year = String(movie["Release Year"] || movie.release_year || "");
        const genre = (movie.Genre || movie.genre || "").toLowerCase();
        const rating = parseFloat(movie["IMDb Rating"] || movie.imdb_rating) || 0;
        const movieId = movie.id || movie.Rank || movie.rank;

        // Watchlist mode check
        if (currentMode === 'watchlist' && !watchlistMovieIds.has(movieId)) {
            return false;
        }

        // Search match (title, year, or genre)
        const matchesSearch = !searchTerm || title.includes(searchTerm) || year.includes(searchTerm) || genre.includes(searchTerm);

        // Genre match
        const matchesGenre = (selectedGenre === "All") || genre.includes(selectedGenre.toLowerCase());

        // Rating match
        const matchesRating = rating >= minRating;

        return matchesSearch && matchesGenre && matchesRating;
    });

    // Sorting logic
    filteredMovies.sort((a, b) => {
        const rankA = parseInt(a.Rank || a.rank) || 999;
        const rankB = parseInt(b.Rank || b.rank) || 999;
        const ratingA = parseFloat(a["IMDb Rating"] || a.imdb_rating) || 0;
        const ratingB = parseFloat(b["IMDb Rating"] || b.imdb_rating) || 0;
        const yearA = parseInt(a["Release Year"] || a.release_year) || 0;
        const yearB = parseInt(b["Release Year"] || b.release_year) || 0;
        const votesA = parseInt(a["Votes Count"] || a.votes_count) || 0;
        const votesB = parseInt(b["Votes Count"] || b.votes_count) || 0;
        const titleA = (a.Title || a.title || "");
        const titleB = (b.Title || b.title || "");

        if (sortVal === "rank-asc") {
            return rankA - rankB;
        } else if (sortVal === "rating-desc") {
            return ratingB - ratingA;
        } else if (sortVal === "year-desc") {
            return yearB - yearA;
        } else if (sortVal === "votes-desc") {
            return votesB - votesA;
        } else if (sortVal === "title-asc") {
            return titleA.localeCompare(titleB);
        }
        return 0;
    });

    renderMovies();
}

// ==========================================================================
// Rendering Movies (Grid Cards & Table Rows)
// ==========================================================================

function renderMovies() {
    const gridView = document.getElementById("moviesGrid");
    const tableBody = document.getElementById("moviesTableBody");
    const noResults = document.getElementById("noResults");

    if (!gridView || !tableBody || !noResults) return;

    if (filteredMovies.length === 0) {
        gridView.innerHTML = "";
        tableBody.innerHTML = "";
        noResults.classList.remove("hidden");
        return;
    }

    noResults.classList.add("hidden");
    const defaultPoster = "https://placehold.co/380x560/F3EDFC/7952B3?text=IMDb+Movie";

    // Render Grid Cards
    gridView.innerHTML = filteredMovies.map(m => {
        const movieId = m.id || m.Rank || m.rank;
        const rank = m.Rank || m.rank;
        const title = m.Title || m.title;
        const year = m["Release Year"] || m.release_year;
        const rating = m["IMDb Rating"] || m.imdb_rating;
        const votes = m.Votes || m.votes || 'N/A';
        const poster = m["Poster Image"] || m.poster_image || defaultPoster;
        const imdbLink = m["IMDb Link"] || m.imdb_link || "#";
        const genre = m.Genre || m.genre || "Drama";
        const isWatchlisted = watchlistMovieIds.has(movieId);

        return `
            <div class="movie-card">
                <div class="poster-wrapper">
                    <span class="rank-badge">#${rank}</span>
                    <span class="rating-badge"><i class="fa-solid fa-star"></i> ${rating}</span>
                    <span class="genre-pill">${genre}</span>
                    <img class="poster-img" src="${poster}" alt="${title}" loading="lazy" onerror="this.onerror=null; this.src='${defaultPoster}';">
                </div>
                <div class="movie-details">
                    <h3 class="movie-title" title="${title}">${title}</h3>
                    <div class="movie-meta">
                        <span><i class="fa-regular fa-calendar"></i> ${year}</span>
                        <span><i class="fa-regular fa-thumbs-up"></i> ${votes}</span>
                    </div>
                    <div class="card-actions-bar">
                        <button class="action-icon-btn ${isWatchlisted ? 'in-watchlist' : ''}" onclick="toggleWatchlist(${movieId})" title="${isWatchlisted ? 'Remove from Watchlist' : 'Add to Watchlist'}">
                            <i class="${isWatchlisted ? 'fa-solid' : 'fa-regular'} fa-heart"></i> ${isWatchlisted ? 'Saved' : 'Watchlist'}
                        </button>
                        <button class="action-icon-btn" onclick="openRecommendationModal(${movieId})" title="AI Recommendations">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> AI Rec
                        </button>
                        <button class="action-icon-btn" onclick="openComparisonWithMovie(${movieId})" title="Compare Movies">
                            <i class="fa-solid fa-scale-balanced"></i> Compare
                        </button>
                    </div>
                    <a href="${imdbLink}" target="_blank" rel="noopener noreferrer" class="imdb-link-btn">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i> View on IMDb
                    </a>
                </div>
            </div>
        `;
    }).join("");

    // Render Table Rows
    tableBody.innerHTML = filteredMovies.map(m => {
        const movieId = m.id || m.Rank || m.rank;
        const rank = m.Rank || m.rank;
        const title = m.Title || m.title;
        const year = m["Release Year"] || m.release_year;
        const rating = m["IMDb Rating"] || m.imdb_rating;
        const votes = m.Votes || m.votes || 'N/A';
        const poster = m["Poster Image"] || m.poster_image || defaultPoster;
        const imdbLink = m["IMDb Link"] || m.imdb_link || "#";
        const genre = m.Genre || m.genre || "Drama";
        const isWatchlisted = watchlistMovieIds.has(movieId);

        return `
            <tr>
                <td class="table-rank">#${rank}</td>
                <td><img class="table-poster" src="${poster}" alt="${title}" loading="lazy" onerror="this.onerror=null; this.src='${defaultPoster}';"></td>
                <td class="table-title">${title}</td>
                <td><span class="genre-pill" style="position:static; display:inline-block; max-width:none;">${genre}</span></td>
                <td>${year}</td>
                <td class="table-rating"><i class="fa-solid fa-star"></i> ${rating}</td>
                <td>${votes}</td>
                <td>
                    <div class="table-actions">
                        <button class="action-icon-btn ${isWatchlisted ? 'in-watchlist' : ''}" onclick="toggleWatchlist(${movieId})" title="Toggle Watchlist">
                            <i class="${isWatchlisted ? 'fa-solid' : 'fa-regular'} fa-heart"></i>
                        </button>
                        <button class="action-icon-btn" onclick="openRecommendationModal(${movieId})" title="AI Recommendations">
                            <i class="fa-solid fa-wand-magic-sparkles"></i>
                        </button>
                        <button class="action-icon-btn" onclick="openComparisonWithMovie(${movieId})" title="Compare">
                            <i class="fa-solid fa-scale-balanced"></i>
                        </button>
                        <a href="${imdbLink}" target="_blank" rel="noopener noreferrer" class="action-icon-btn" title="View on IMDb">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// Switch between Grid and Table View
function switchView(view) {
    currentView = view;
    const gridBtn = document.getElementById("gridViewBtn");
    const tableBtn = document.getElementById("tableViewBtn");
    const gridView = document.getElementById("moviesGrid");
    const tableWrapper = document.getElementById("moviesTableWrapper");

    if (!gridBtn || !tableBtn || !gridView || !tableWrapper) return;

    if (view === 'grid') {
        gridBtn.classList.add("active");
        tableBtn.classList.remove("active");
        gridView.classList.remove("hidden");
        tableWrapper.classList.add("hidden");
    } else {
        tableBtn.classList.add("active");
        gridBtn.classList.remove("active");
        tableWrapper.classList.remove("hidden");
        gridView.classList.add("hidden");
    }
}

// ==========================================================================
// AI Recommendations Modal (TF-IDF & Cosine Similarity)
// ==========================================================================

async function openRecommendationModal(movieId) {
    const modal = document.getElementById("recommendationModal");
    const titleEl = document.getElementById("recTargetTitle");
    const container = document.getElementById("recResultsContainer");

    if (!modal || !titleEl || !container) return;

    // Locate target movie in memory
    const target = allMovies.find(m => (m.id == movieId || m.Rank == movieId || m.rank == movieId));
    if (target) {
        titleEl.textContent = `${target.Title || target.title} (#${target.Rank || target.rank}, ${target["Release Year"] || target.release_year})`;
    } else {
        titleEl.textContent = `Target Film #${movieId}`;
    }

    modal.classList.remove("hidden");
    container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; color: var(--button-primary);">
            <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2rem;"></i>
            <p style="margin-top: 0.8rem; font-weight: 600;">Computing TF-IDF Vectors & Cosine Similarities...</p>
        </div>
    `;

    try {
        const response = await fetch(`/api/recommendations/${movieId}?limit=6`);
        const data = await response.json();

        if (data.status === "success" && Array.isArray(data.recommendations)) {
            if (data.target_movie_title) {
                titleEl.textContent = `${data.target_movie_title} (#${data.target_movie_rank || 'N/A'})`;
            }

            const defaultPoster = "https://placehold.co/380x560/F3EDFC/7952B3?text=IMDb+Movie";

            container.innerHTML = data.recommendations.map(rec => {
                const recId = rec.id || rec.rank;
                const isWatchlisted = watchlistMovieIds.has(recId);
                return `
                    <div class="rec-card">
                        <div class="rec-badge-score">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> ${rec.match_percentage} Match
                        </div>
                        <div style="display: flex; gap: 0.75rem; align-items: center;">
                            <img src="${rec.poster_image || defaultPoster}" alt="${rec.title}" style="width: 48px; height: 68px; object-fit: cover; border-radius: 6px;" onerror="this.onerror=null; this.src='${defaultPoster}';">
                            <div>
                                <h4 class="rec-title">#${rec.rank} ${rec.title}</h4>
                                <p class="rec-meta"><i class="fa-regular fa-calendar"></i> ${rec.release_year} • <i class="fa-solid fa-star" style="color:var(--gold-star)"></i> ${rec.imdb_rating}</p>
                            </div>
                        </div>
                        <div class="rec-reason">${rec.explanation}</div>
                        <div style="display: flex; gap: 0.4rem; margin-top: auto; padding-top: 0.4rem;">
                            <button class="action-icon-btn ${isWatchlisted ? 'in-watchlist' : ''}" onclick="toggleWatchlist(${recId})" style="flex: 1;" title="Save to Watchlist">
                                <i class="${isWatchlisted ? 'fa-solid' : 'fa-regular'} fa-heart"></i> ${isWatchlisted ? 'Saved' : 'Watchlist'}
                            </button>
                            <a href="${rec.imdb_link || '#'}" target="_blank" rel="noopener noreferrer" class="action-icon-btn" style="flex: 1;" title="View on IMDb">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i> IMDb
                            </a>
                        </div>
                    </div>
                `;
            }).join("");
        } else {
            container.innerHTML = `<p style="grid-column: 1 / -1; text-align: center; color: var(--danger-red);">Could not calculate recommendations.</p>`;
        }
    } catch (err) {
        console.error("AI recommendations error:", err);
        container.innerHTML = `<p style="grid-column: 1 / -1; text-align: center; color: var(--danger-red);">Failed to connect to recommendation service.</p>`;
    }
}

// ==========================================================================
// Head-to-Head Movie Comparison Modal
// ==========================================================================

function populateComparisonSelects() {
    const sel1 = document.getElementById("compMovie1Select");
    const sel2 = document.getElementById("compMovie2Select");
    if (!sel1 || !sel2 || allMovies.length === 0) return;

    // Preserve selections if already set
    const currentVal1 = sel1.value;
    const currentVal2 = sel2.value;

    const optionsHtml = allMovies.map(m => {
        const id = m.id || m.Rank || m.rank;
        const rank = m.Rank || m.rank;
        const title = m.Title || m.title;
        const year = m["Release Year"] || m.release_year;
        return `<option value="${id}">#${rank} - ${title} (${year})</option>`;
    }).join("");

    sel1.innerHTML = optionsHtml;
    sel2.innerHTML = optionsHtml;

    if (currentVal1) {
        sel1.value = currentVal1;
    } else if (allMovies.length > 0) {
        sel1.value = allMovies[0].id || allMovies[0].Rank || 1;
    }

    if (currentVal2) {
        sel2.value = currentVal2;
    } else if (allMovies.length > 1) {
        sel2.value = allMovies[1].id || allMovies[1].Rank || 2;
    }
}

function openComparisonWithMovie(movieId) {
    const modal = document.getElementById("comparisonModal");
    const sel1 = document.getElementById("compMovie1Select");
    const sel2 = document.getElementById("compMovie2Select");

    if (modal) modal.classList.remove("hidden");
    if (sel1 && movieId) {
        sel1.value = movieId;
        // Make sure second select doesn't match first
        if (sel2 && sel2.value == movieId && allMovies.length > 1) {
            const alternate = allMovies.find(m => (m.id || m.Rank) != movieId);
            if (alternate) sel2.value = alternate.id || alternate.Rank;
        }
    }

    runComparison();
}

async function runComparison() {
    const sel1 = document.getElementById("compMovie1Select");
    const sel2 = document.getElementById("compMovie2Select");
    const verdictText = document.getElementById("compVerdictText");
    const colTitle1 = document.getElementById("compColTitle1");
    const colTitle2 = document.getElementById("compColTitle2");
    const tableBody = document.getElementById("compTableBody");

    if (!sel1 || !sel2 || !verdictText || !tableBody) return;

    const id1 = sel1.value;
    const id2 = sel2.value;

    if (id1 === id2) {
        verdictText.innerHTML = `<span style="color:var(--danger-red); font-weight:700;"><i class="fa-solid fa-triangle-exclamation"></i> Please select two different movies to compare.</span>`;
        tableBody.innerHTML = "";
        return;
    }

    verdictText.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing movie statistics & cosine distance...`;

    try {
        const response = await fetch(`/api/movies/compare?movie1_id=${id1}&movie2_id=${id2}`);
        const data = await response.json();

        if (data.status === "success" && data.metrics_table) {
            verdictText.textContent = data.verdict;

            const title1 = data.movie1.Title || data.movie1.title;
            const rank1 = data.movie1.Rank || data.movie1.rank;
            const title2 = data.movie2.Title || data.movie2.title;
            const rank2 = data.movie2.Rank || data.movie2.rank;

            if (colTitle1) colTitle1.textContent = `#${rank1} ${title1}`;
            if (colTitle2) colTitle2.textContent = `#${rank2} ${title2}`;

            tableBody.innerHTML = data.metrics_table.map(row => `
                <tr>
                    <td style="font-weight: 700; color: var(--button-primary);">${row.metric}</td>
                    <td>${row.movie1_value}</td>
                    <td>${row.movie2_value}</td>
                    <td><span class="sidebar-pill" style="display: inline-block; padding: 0.25rem 0.6rem;">${row.advantage}</span></td>
                </tr>
            `).join("");
        } else {
            verdictText.textContent = "Failed to generate comparison.";
        }
    } catch (err) {
        console.error("Comparison error:", err);
        verdictText.textContent = "Error executing comparison analysis.";
    }
}

// ==========================================================================
// Data Quality & Duplicate Detection Modal
// ==========================================================================

async function openDataQualityModal() {
    const modal = document.getElementById("validationModal");
    const scoreNum = document.getElementById("healthScoreNum");
    const statusText = document.getElementById("healthStatusText");
    const descText = document.getElementById("healthDescText");
    const dupesBox = document.getElementById("dupesResultBox");

    if (modal) modal.classList.remove("hidden");
    if (dupesBox) dupesBox.classList.add("hidden");

    try {
        const response = await fetch("/api/dataset/validate");
        const data = await response.json();

        if (data.status === "success") {
            if (scoreNum) scoreNum.textContent = `${data.health_score}%`;
            if (statusText) statusText.textContent = data.status === "Healthy" ? "Dataset in Pristine Condition" : "Dataset Needs Attention";
            if (descText) {
                descText.textContent = `Scanned ${data.total_records} records. Missing Titles: ${data.metrics.missing_titles}, Rating Anomalies: ${data.metrics.invalid_ratings}, Poster Issues: ${data.metrics.missing_posters}.`;
            }
        }
    } catch (err) {
        console.error("Data quality error:", err);
    }
}

async function handleCheckDuplicates() {
    const dupesBox = document.getElementById("dupesResultBox");
    if (!dupesBox) return;

    dupesBox.classList.remove("hidden");
    dupesBox.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Scanning dataset for duplicate movie titles...`;

    try {
        const response = await fetch("/api/dataset/duplicates");
        const data = await response.json();

        if (data.status === "success") {
            if (data.duplicate_count === 0) {
                dupesBox.innerHTML = `
                    <div style="color: var(--success-green); font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Zero duplicate records detected! All 250 movie titles are unique.</span>
                    </div>
                `;
            } else {
                let html = `
                    <div style="color: var(--button-primary); font-weight: 700; margin-bottom: 0.5rem;">
                        <i class="fa-solid fa-triangle-exclamation" style="color: var(--gold-star);"></i>
                        Found ${data.duplicate_count} duplicate record(s):
                    </div>
                    <ul style="margin-left: 1.25rem; font-size: 0.85rem; color: var(--text-primary);">
                `;
                for (const [title, ids] of Object.entries(data.duplicates || {})) {
                    html += `<li><strong>${title}</strong> (IDs: ${ids.join(", ")})</li>`;
                }
                html += `</ul>
                    <button id="btnDeduplicateAction" class="btn btn-primary btn-sm mt-3" style="width: 100%;">
                        <i class="fa-solid fa-broom"></i> Remove Duplicates & Clean Dataset
                    </button>
                `;
                dupesBox.innerHTML = html;

                const dedupBtn = document.getElementById("btnDeduplicateAction");
                if (dedupBtn) {
                    dedupBtn.addEventListener("click", handleDeduplicateDataset);
                }
            }
        }
    } catch (err) {
        console.error("Duplicates scan error:", err);
        dupesBox.innerHTML = `<span style="color: var(--danger-red);">Failed to scan for duplicate records.</span>`;
    }
}

async function handleDeduplicateDataset() {
    const dupesBox = document.getElementById("dupesResultBox");
    if (dupesBox) dupesBox.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Deduplicating dataset...`;

    try {
        const response = await fetch("/api/dataset/deduplicate", { method: "POST" });
        const data = await response.json();
        if (data.status === "success") {
            showToast(data.message, "success");
            await fetchMovies();
            await fetchStats();
            openDataQualityModal();
        } else {
            showToast("Failed to clean duplicates.", "error");
        }
    } catch (err) {
        console.error("Deduplication error:", err);
        showToast("Error executing deduplication.", "error");
    }
}

// ==========================================================================
// Scraper Trigger
// ==========================================================================

async function handleRunScraper() {
    const loadingOverlay = document.getElementById("loadingOverlay");
    if (loadingOverlay) loadingOverlay.classList.remove("hidden");

    try {
        const response = await fetch("/api/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ use_selenium: false, limit: 250 })
        });
        const data = await response.json();
        if (data.status === "success") {
            await fetchMovies();
            await fetchStats();
            showToast(`Scrape complete! Successfully synced ${data.count} movies into database.`, "success");
        } else {
            showToast("Scraper completed with fallback data.", "info");
            await fetchMovies();
            await fetchStats();
        }
    } catch (err) {
        console.error("Scraper error:", err);
        showToast("Failed to run scraper service.", "error");
    } finally {
        if (loadingOverlay) loadingOverlay.classList.add("hidden");
    }
}

// ==========================================================================
// CSV and Excel File Upload
// ==========================================================================

async function handleFileUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("csvFileInput");
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a .csv or .xlsx file first.", "error");
        return;
    }

    const file = fileInput.files[0];
    const fileName = file.name.toLowerCase();
    const isExcel = fileName.endsWith(".xlsx") || fileName.endsWith(".xls");
    const isCSV = fileName.endsWith(".csv");

    if (!isExcel && !isCSV) {
        showToast("Only .csv and .xlsx Excel files are supported.", "error");
        return;
    }

    const endpoint = isExcel ? "/api/upload/excel" : "/api/upload/csv";
    const formData = new FormData();
    formData.append("file", file);

    const uploadModal = document.getElementById("uploadModal");
    showToast(`Uploading and validating ${file.name}...`, "info");

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (data.status === "success") {
            if (uploadModal) uploadModal.classList.add("hidden");
            await fetchMovies();
            await fetchStats();
            showToast(data.message || `Successfully ingested ${data.count} movies!`, "success");
        } else {
            showToast(data.detail || data.message || "Upload failed validation.", "error");
        }
    } catch (err) {
        console.error("Upload error:", err);
        showToast("Error uploading dataset file.", "error");
    }
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("input", applyFilters);
    }

    // Genre filter
    const genreFilter = document.getElementById("genreFilter");
    if (genreFilter) {
        genreFilter.addEventListener("change", applyFilters);
    }

    // Rating filter
    const ratingFilter = document.getElementById("ratingFilter");
    if (ratingFilter) {
        ratingFilter.addEventListener("change", applyFilters);
    }

    // Sort By
    const sortBy = document.getElementById("sortBy");
    if (sortBy) {
        sortBy.addEventListener("change", applyFilters);
    }

    // Mode Tabs: All vs Watchlist
    const tabAllMovies = document.getElementById("tabAllMovies");
    const tabWatchlist = document.getElementById("tabWatchlist");

    if (tabAllMovies && tabWatchlist) {
        tabAllMovies.addEventListener("click", () => {
            currentMode = 'all';
            tabAllMovies.classList.add("active");
            tabWatchlist.classList.remove("active");
            applyFilters();
        });

        tabWatchlist.addEventListener("click", () => {
            currentMode = 'watchlist';
            tabWatchlist.classList.add("active");
            tabAllMovies.classList.remove("active");
            applyFilters();
        });
    }

    // Chart toggle pills
    const chartDecadeBtn = document.getElementById("chartDecadeBtn");
    const chartGenreBtn = document.getElementById("chartGenreBtn");
    const chartRatingBtn = document.getElementById("chartRatingBtn");

    if (chartDecadeBtn) chartDecadeBtn.addEventListener("click", () => switchChartType('decade'));
    if (chartGenreBtn) chartGenreBtn.addEventListener("click", () => switchChartType('genre'));
    if (chartRatingBtn) chartRatingBtn.addEventListener("click", () => switchChartType('rating'));

    // View Toggles: Grid vs Table
    const gridViewBtn = document.getElementById("gridViewBtn");
    const tableViewBtn = document.getElementById("tableViewBtn");
    if (gridViewBtn) gridViewBtn.addEventListener("click", () => switchView('grid'));
    if (tableViewBtn) tableViewBtn.addEventListener("click", () => switchView('table'));

    // Comparison select change handlers
    const compMovie1Select = document.getElementById("compMovie1Select");
    const compMovie2Select = document.getElementById("compMovie2Select");
    if (compMovie1Select) compMovie1Select.addEventListener("change", runComparison);
    if (compMovie2Select) compMovie2Select.addEventListener("change", runComparison);

    // Scraper Buttons (Navbar & Sidebar)
    const scrapeBtn = document.getElementById("scrapeBtn");
    const sidebarScrapeBtn = document.getElementById("sidebarScrapeBtn");
    if (scrapeBtn) scrapeBtn.addEventListener("click", handleRunScraper);
    if (sidebarScrapeBtn) sidebarScrapeBtn.addEventListener("click", handleRunScraper);

    // CSV & Excel Upload Modal Handlers
    const uploadModal = document.getElementById("uploadModal");
    const uploadModalBtn = document.getElementById("uploadModalBtn");
    const sidebarUploadBtn = document.getElementById("sidebarUploadBtn");
    const closeModalBtn = document.getElementById("closeModalBtn");

    if (uploadModalBtn && uploadModal) {
        uploadModalBtn.addEventListener("click", () => uploadModal.classList.remove("hidden"));
    }
    if (sidebarUploadBtn && uploadModal) {
        sidebarUploadBtn.addEventListener("click", () => {
            uploadModal.classList.remove("hidden");
            closeMobileSidebar();
        });
    }
    if (closeModalBtn && uploadModal) {
        closeModalBtn.addEventListener("click", () => uploadModal.classList.add("hidden"));
    }

    // AI Recommendation Modal Close Handler
    const recModal = document.getElementById("recommendationModal");
    const closeRecModalBtn = document.getElementById("closeRecModalBtn");
    if (closeRecModalBtn && recModal) {
        closeRecModalBtn.addEventListener("click", () => recModal.classList.add("hidden"));
    }

    // Comparison Modal Close & Open Handlers
    const compModal = document.getElementById("comparisonModal");
    const closeCompModalBtn = document.getElementById("closeCompModalBtn");
    const navLinkCompare = document.getElementById("navLinkCompare");
    if (closeCompModalBtn && compModal) {
        closeCompModalBtn.addEventListener("click", () => compModal.classList.add("hidden"));
    }
    if (navLinkCompare) {
        navLinkCompare.addEventListener("click", () => {
            if (compModal) compModal.classList.remove("hidden");
            closeMobileSidebar();
            runComparison();
        });
    }

    // Data Quality & Duplicate Detection Handlers
    const valModal = document.getElementById("validationModal");
    const closeValModalBtn = document.getElementById("closeValModalBtn");
    const navLinkHealth = document.getElementById("navLinkHealth");
    const btnCheckDuplicates = document.getElementById("btnCheckDuplicates");

    if (closeValModalBtn && valModal) {
        closeValModalBtn.addEventListener("click", () => valModal.classList.add("hidden"));
    }
    if (navLinkHealth) {
        navLinkHealth.addEventListener("click", () => {
            openDataQualityModal();
            closeMobileSidebar();
        });
    }
    if (btnCheckDuplicates) {
        btnCheckDuplicates.addEventListener("click", handleCheckDuplicates);
    }

    // Sidebar navigation link actions
    const navLinkDashboard = document.getElementById("navLinkDashboard");
    const navLinkAnalytics = document.getElementById("navLinkAnalytics");
    const navLinkMovies = document.getElementById("navLinkMovies");
    const navLinkWatchlist = document.getElementById("navLinkWatchlist");

    if (navLinkMovies) {
        navLinkMovies.addEventListener("click", () => {
            currentMode = 'all';
            if (tabAllMovies) tabAllMovies.classList.add("active");
            if (tabWatchlist) tabWatchlist.classList.remove("active");
            applyFilters();
            closeMobileSidebar();
        });
    }

    if (navLinkWatchlist) {
        navLinkWatchlist.addEventListener("click", () => {
            currentMode = 'watchlist';
            if (tabWatchlist) tabWatchlist.classList.add("active");
            if (tabAllMovies) tabAllMovies.classList.remove("active");
            applyFilters();
            closeMobileSidebar();
        });
    }

    // File Drag & Drop
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("csvFileInput");
    const fileNameDisplay = document.getElementById("fileNameDisplay");

    if (dropZone && fileInput) {
        dropZone.addEventListener("click", () => fileInput.click());
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
        dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                if (fileNameDisplay) fileNameDisplay.textContent = e.dataTransfer.files[0].name;
            }
        });
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0 && fileNameDisplay) {
                fileNameDisplay.textContent = fileInput.files[0].name;
            }
        });
    }

    // Form Submit for Upload
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", handleFileUpload);
    }

    // Mobile Sidebar Drawer Controls
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            if (sidebarBackdrop) sidebarBackdrop.classList.toggle("visible");
        });
    }
    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener("click", closeMobileSidebar);
    }
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", closeMobileSidebar);
    }

    // Close Modals on Outside Backdrop Click
    [uploadModal, recModal, compModal, valModal].forEach(m => {
        if (m) {
            m.addEventListener("click", (e) => {
                if (e.target === m) {
                    m.classList.add("hidden");
                }
            });
        }
    });

    // Escape Key Handler for All Modals & Sidebar
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            [uploadModal, recModal, compModal, valModal].forEach(m => {
                if (m && !m.classList.contains("hidden")) {
                    m.classList.add("hidden");
                }
            });
            closeMobileSidebar();
        }
    });
}

function closeMobileSidebar() {
    const sidebar = document.getElementById("sidebar");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");
    if (sidebar) sidebar.classList.remove("open");
    if (sidebarBackdrop) sidebarBackdrop.classList.remove("visible");
}

// ==========================================================================
// Toast Notifications
// ==========================================================================

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-triangle-exclamation';
    else if (type === 'info') iconClass = 'fa-circle-info';

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 350);
    }, 4000);
}
