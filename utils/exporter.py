"""Generate downloadable DOCX / PDF output for the optimized resume
and cover letter.

IMPORTANT, read before assuming this is pixel-perfect: `text_to_docx`
and `text_to_pdf` below build a brand-new, clean, single-column
document from scratch -- they do NOT preserve your original resume's
exact fonts, spacing, or page count. That's what caused a "disoriented"
export before. For DOCX-uploaded resumes, use
`apply_bullet_replacements_to_docx` instead: it edits your ORIGINAL
file in place, replacing only the specific bullet text that changed,
so everything else (fonts, margins, page count, bullet style) stays
exactly as it was. There is no equivalent for PDF-uploaded resumes --
PDF text extraction loses layout information, so a PDF original can
only get the clean-rebuild export, never a true in-place edit.
"""

from __future__ import annotations

import io
import re

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def apply_bullet_replacements_to_docx(original_bytes: bytes, bullet_map: dict[str, str]) -> bytes:
    """Edit the ORIGINAL uploaded docx in place.

    `bullet_map` maps original bullet text -> rewritten text. Only
    paragraphs that match a key get touched; everything else in the
    document (fonts, spacing, headers, other sections) is untouched.

    Trade-off: when a matched paragraph has multiple runs (e.g. a bold
    word mid-bullet), we keep the first run's formatting and collapse
    the rest, so any formatting inside the bullet itself is simplified
    to the first run's style. This is the standard trade-off for
    editing rich text without a full diffing engine.
    """
    doc = Document(io.BytesIO(original_bytes))
    norm_map = {_norm(k): v for k, v in bullet_map.items() if k.strip()}

    for para in doc.paragraphs:
        p_norm = _norm(para.text)
        if not p_norm:
            continue
        match_key = next((k for k in norm_map if k == p_norm or (len(k) > 20 and (k in p_norm or p_norm in k))), None)
        if not match_key:
            continue
        new_text = norm_map[match_key]
        if para.runs:
            para.runs[0].text = new_text
            for extra in para.runs[1:]:
                extra.text = ""
        else:
            para.add_run(new_text)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


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
