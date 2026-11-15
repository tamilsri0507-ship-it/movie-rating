"""PDF Report Generation Router."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.pdf_service import generate_cinescope_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports & Exports"])


@router.get("/pdf", summary="Generate professional CineScope AI PDF Analytics Report")
def export_pdf_report(db: Session = Depends(get_db)):
    """
    Generates a PDF document with ReportLab in the CineScope AI Light Lavender & Soft Purple theme.
    Contains summary KPIs, era breakdown table, genre distribution table, and top movie list.
    """
    pdf_buffer = generate_cinescope_pdf(db)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=CineScope_AI_Analytics_Report.pdf"
        }
    )
