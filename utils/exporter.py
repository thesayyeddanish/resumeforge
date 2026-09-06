"""Generate downloadable DOCX / PDF output for the optimized resume
and cover letter. Kept intentionally simple/clean so it renders
predictably in ATS parsers (single column, standard fonts, no tables
or text boxes).
"""

from __future__ import annotations

import io

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def text_to_docx(title: str, body_text: str) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    if title:
        heading = doc.add_heading(title, level=1)

    for para in body_text.split("\n"):
        if para.strip() == "":
            doc.add_paragraph("")
        else:
            doc.add_paragraph(para)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def text_to_pdf(title: str, body_text: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14)
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=16, spaceAfter=14)

    story = []
    if title:
        story.append(Paragraph(title, title_style))

    for para in body_text.split("\n"):
        if para.strip() == "":
            story.append(Spacer(1, 8))
        else:
            safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body_style))

    doc.build(story)
    return buf.getvalue()
