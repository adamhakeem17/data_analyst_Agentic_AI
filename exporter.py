"""PDF export for the analysis session."""

from __future__ import annotations

from datetime import datetime
from typing import List

from fpdf import FPDF


def to_pdf_bytes(chat_history: List[dict], dataset_name: str, row_count: int) -> bytes:
    """Render the chat session as a downloadable PDF report."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "AI Data Analysis Report", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(
        0, 7,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
        f"Dataset: {dataset_name}  |  Rows: {row_count:,}",
        ln=True,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Conversation
    for msg in chat_history:
        if msg["role"] == "user":
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(30, 30, 60)
            pdf.multi_cell(0, 8, _safe(f"Q: {msg['content']}"), fill=True)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 7, _safe(msg["content"]))
            pdf.ln(5)

    return bytes(pdf.output())


def _safe(text: str) -> str:
    """Handle characters outside fpdf's default latin-1 range."""
    return text.encode("latin-1", errors="replace").decode("latin-1")
