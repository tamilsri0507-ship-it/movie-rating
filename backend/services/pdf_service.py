"""PDF Report Generation Service using ReportLab in CineScope AI Lavender Theme."""

import io
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.models.movie import Movie
from backend.services.analytics_service import (
    compute_summary_stats,
    compute_decade_distribution,
    compute_genre_distribution
)

# CineScope AI Theme Colors
COLOR_BG_LAVENDER = colors.HexColor("#F7F3FF")
COLOR_PRIMARY = colors.HexColor("#B99AFF")
COLOR_LAVENDER_LIGHT = colors.HexColor("#E6D9FF")
COLOR_PURPLE = colors.HexColor("#7952B3")
COLOR_TEXT = colors.HexColor("#29213A")
COLOR_BORDER = colors.HexColor("#E8DDF8")
COLOR_WHITE = colors.HexColor("#FFFFFF")


def generate_cinescope_pdf(db: Session) -> io.BytesIO:
    """Generate a clean, high-quality PDF analytics report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "CineScopeTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=COLOR_PURPLE
    )

    subtitle_style = ParagraphStyle(
        "CineScopeSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=COLOR_TEXT
    )

    heading2_style = ParagraphStyle(
        "CineScopeH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=COLOR_PURPLE,
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "CineScopeBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=COLOR_TEXT
    )

    body_bold = ParagraphStyle(
        "CineScopeBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=COLOR_TEXT
    )

    # 1. Header Banner
    story.append(Paragraph("CineScope AI • Executive Film Intelligence Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} | Database: IMDb Top 250 Curated Collection",
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY, spaceBefore=4, spaceAfter=14))

    # 2. Executive Summary Metrics
    stats = compute_summary_stats(db)
    summary_data = [
        [
            Paragraph("<b>Total Movies</b>", body_style),
            Paragraph("<b>Average Rating</b>", body_style),
            Paragraph("<b>Top Rated Film</b>", body_style),
            Paragraph("<b>Dominant Era</b>", body_style)
        ],
        [
            Paragraph(f"<font size=14 color='#7952B3'><b>{stats['total_movies']}</b></font>", body_style),
            Paragraph(f"<font size=14 color='#7952B3'><b>{stats['avg_rating']} / 10</b></font>", body_style),
            Paragraph(f"<font size=11 color='#29213A'><b>{stats['top_movie']}</b> ({stats['top_rating']})</font>", body_style),
            Paragraph(f"<font size=14 color='#7952B3'><b>{stats['top_decade']}</b></font>", body_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[1.7 * inch, 1.7 * inch, 2.5 * inch, 1.6 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_LAVENDER_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("BOX", (0, 0), (-1, -1), 1.5, COLOR_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # 3. Era & Decade Distribution
    story.append(Paragraph("1. Decade Concentration & Era Breakdown", heading2_style))
    decade_stats = compute_decade_distribution(db)
    decade_rows = [
        [
            Paragraph("<b>Decade</b>", body_bold),
            Paragraph("<b>Movies Count</b>", body_bold),
            Paragraph("<b>Avg IMDb Rating</b>", body_bold),
            Paragraph("<b>Top Ranked Movie</b>", body_bold),
            Paragraph("<b>Top Rating</b>", body_bold)
        ]
    ]
    for d in decade_stats:
        decade_rows.append([
            Paragraph(d["decade"], body_style),
            Paragraph(str(d["count"]), body_style),
            Paragraph(f"{d['avg_rating']:.2f}", body_style),
            Paragraph(d["top_movie"], body_style),
            Paragraph(str(d["top_rating"]), body_style)
        ])

    decade_table = Table(decade_rows, colWidths=[1.1 * inch, 1.2 * inch, 1.3 * inch, 2.9 * inch, 1.0 * inch])
    decade_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LAVENDER]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(decade_table)
    story.append(Spacer(1, 14))

    # 4. Genre Breakdown
    story.append(Paragraph("2. Top Film Genres Distribution", heading2_style))
    genre_stats = compute_genre_distribution(db)[:8]
    genre_rows = [
        [
            Paragraph("<b>Genre</b>", body_bold),
            Paragraph("<b>Count</b>", body_bold),
            Paragraph("<b>Market Share</b>", body_bold),
            Paragraph("<b>Avg Rating</b>", body_bold),
            Paragraph("<b>Exemplary Title</b>", body_bold)
        ]
    ]
    for g in genre_stats:
        genre_rows.append([
            Paragraph(g["genre"], body_style),
            Paragraph(str(g["count"]), body_style),
            Paragraph(f"{g['percentage']}%", body_style),
            Paragraph(f"{g['avg_rating']:.2f}", body_style),
            Paragraph(g["top_movie"], body_style)
        ])

    genre_table = Table(genre_rows, colWidths=[1.5 * inch, 1.0 * inch, 1.2 * inch, 1.2 * inch, 2.6 * inch])
    genre_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LAVENDER]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(genre_table)
    story.append(Spacer(1, 14))

    # 5. Top 30 Highest Rated Films
    story.append(Paragraph("3. Top 30 Highest-Ranked Masterpieces", heading2_style))
    top_30_movies = db.query(Movie).order_by(Movie.rank.asc()).limit(30).all()
    top_rows = [
        [
            Paragraph("<b>Rank</b>", body_bold),
            Paragraph("<b>Movie Title</b>", body_bold),
            Paragraph("<b>Year</b>", body_bold),
            Paragraph("<b>Rating</b>", body_bold),
            Paragraph("<b>Total Votes</b>", body_bold),
            Paragraph("<b>Genre</b>", body_bold)
        ]
    ]
    for m in top_30_movies:
        top_rows.append([
            Paragraph(f"#{m.rank}", body_style),
            Paragraph(m.title, body_bold),
            Paragraph(str(m.release_year), body_style),
            Paragraph(f"★ {m.imdb_rating}", body_style),
            Paragraph(m.votes, body_style),
            Paragraph(m.genre or "Drama", body_style)
        ])

    top_table = Table(top_rows, colWidths=[0.6 * inch, 2.6 * inch, 0.7 * inch, 0.8 * inch, 1.1 * inch, 1.7 * inch])
    top_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LAVENDER]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(top_table)

    # 6. Report Footer
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "CineScope AI • Python FastAPI & SQLite High-Performance Analytics Backend • Designed with Light Lavender & Soft Purple Theme",
        body_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
