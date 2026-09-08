"""Extract raw text (and light structure) from uploaded resumes.

Supports PDF and DOCX. Returns plain text plus a naive section map so
downstream scoring/AI modules don't each re-implement parsing.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import docx2txt
import pdfplumber


SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "objective", "profile"],
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core competencies", "key skills"],
    "projects": ["projects", "personal projects", "academic projects"],
    "certifications": ["certifications", "licenses", "certificates"],
}


@dataclass
class ParsedResume:
    raw_text: str
    lines: list[str]
    sections: dict[str, str] = field(default_factory=dict)
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    has_photo_or_table: bool = False  # ATS risk flag (PDF only, best-effort)


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, bool]:
    text_parts = []
    has_images_or_tables = False
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
            if page.images:
                has_images_or_tables = True
            if page.find_tables():
                has_images_or_tables = True
    return "\n".join(text_parts), has_images_or_tables


def extract_text_from_docx(file_bytes: bytes) -> str:
    return docx2txt.process(io.BytesIO(file_bytes)) or ""


def _find_contact_fields(text: str) -> tuple[str | None, str | None, str | None]:
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(
        r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}", text
    )
    linkedin_match = re.search(r"(linkedin\.com/in/[A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
    return (
        email_match.group(0) if email_match else None,
        phone_match.group(0).strip() if phone_match else None,
        linkedin_match.group(0) if linkedin_match else None,
    )


def _split_into_sections(text: str) -> dict[str, str]:
    lines = text.split("\n")
    normalized = [re.sub(r"[^a-z ]", "", l.lower()).strip() for l in lines]

    header_to_canonical = {}
    for canonical, variants in SECTION_HEADERS.items():
        for v in variants:
            header_to_canonical[v] = canonical

    boundaries = []  # (line_index, canonical_name)
    for i, norm_line in enumerate(normalized):
        if not norm_line or len(norm_line.split()) > 5:
            continue
        if norm_line in header_to_canonical:
            boundaries.append((i, header_to_canonical[norm_line]))

    sections: dict[str, str] = {}
    for idx, (start, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        sections[name] = "\n".join(lines[start + 1 : end]).strip()

    return sections


def _sanitize_text(text: str) -> str:
    """Fix known "tofu glyph" artifacts from PDFs with quirky embedded fonts.

    Some resume PDFs (often ones exported from certain design tools)
    encode their hyphen glyph in a way that extracts as a black-square
    placeholder instead of "-" -- e.g. "pre■game" instead of "pre-game".
    This shows up not just on screen but as literal black boxes in
    DOCX/PDF exports, since the export font has no glyph for it either.
    Replacing these with a plain hyphen fixes it everywhere downstream.
    """
    for bad_char in ("■", "▪", "◾", "\uf0b7", "\uf0a7", "\ufffd", "\x96", "\x97"):
        text = text.replace(bad_char, "-")
    return text


def parse_resume(file_bytes: bytes, filename: str) -> ParsedResume:
    filename_lower = filename.lower()
    has_visual_risk = False

    if filename_lower.endswith(".pdf"):
        raw_text, has_visual_risk = extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

    raw_text = _sanitize_text(raw_text.replace("\r", ""))
    lines = [l for l in raw_text.split("\n")]
    email, phone, linkedin = _find_contact_fields(raw_text)
    sections = _split_into_sections(raw_text)

    return ParsedResume(
        raw_text=raw_text,
        lines=lines,
        sections=sections,
        email=email,
        phone=phone,
        linkedin=linkedin,
        has_photo_or_table=has_visual_risk,
    )
