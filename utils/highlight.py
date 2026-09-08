"""Highlight matched keywords inline within a block of resume text."""

from __future__ import annotations

import html as _html
import re


def highlight_matches(text: str, keywords: list[str]) -> str:
    """HTML-escape `text`, then wrap any matched keyword in a <mark>.

    Longest keywords are matched first so multi-word terms ("machine
    learning") aren't partially shadowed by shorter overlapping ones.
    """
    escaped = _html.escape(text)
    seen = sorted({k.strip() for k in keywords if k and k.strip()}, key=len, reverse=True)

    for kw in seen:
        kw_escaped = _html.escape(kw)
        if not kw_escaped:
            continue
        pattern = re.compile(r"(?<![\w-])(" + re.escape(kw_escaped) + r")(?![\w-])", re.IGNORECASE)
        escaped = pattern.sub(r"<mark class='gf-hit'>\1</mark>", escaped)

    return escaped.replace("\n", "<br>")
