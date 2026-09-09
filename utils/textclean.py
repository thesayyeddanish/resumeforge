"""Text sanitization used everywhere text enters or leaves the app.

Some resume PDFs have a font-encoding quirk where a hyphen decodes as
a black-square placeholder (e.g. "pre■game" instead of "pre-game").
That alone was fixed by cleaning the resume at upload time -- but the
AI can then *pattern-match* on that character if it ever sees it in
context (or in rare cases produce an unrelated unsupported glyph on
its own), reproducing it in newly-generated bullets/cover letters that
never went through the upload-time cleaning. So this same cleanup now
runs at THREE points: right after resume upload, right after every AI
response, and right before anything is written to a DOCX/PDF export --
belt and suspenders, so nothing slips through.
"""

from __future__ import annotations

_BAD_CHARS = ("■", "▪", "◾", "\uf0b7", "\uf0a7", "\ufffd", "\x96", "\x97")


def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    for bad_char in _BAD_CHARS:
        text = text.replace(bad_char, "-")
    return text


def sanitize_deep(obj):
    """Recursively sanitize every string inside a dict/list structure
    (used for AI JSON responses, which nest strings inside lists/dicts)."""
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, list):
        return [sanitize_deep(item) for item in obj]
    if isinstance(obj, dict):
        return {k: sanitize_deep(v) for k, v in obj.items()}
    return obj
