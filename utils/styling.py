"""Design system for ResumeForge AI.

Light glass theme: soft lavender-white background, frosted white cards,
purple/cyan gradient accents. Everything visual funnels through here.

Every page should call `inject_css()` once at the top, and use
`render()` (never raw `st.markdown(..., unsafe_allow_html=True)`) for
HTML snippets -- `render()` strips leading whitespace from every line
first, which fixes a real Streamlit bug where indented HTML gets
treated as a Markdown code block and shown as literal text.
"""

from __future__ import annotations

import streamlit as st

# --- Palette (light glass) ----------------------------------------------------
BG = "#F5F6FB"
SURFACE = "#FFFFFF"          # opaque -- used for donut holes etc.
CARD = "rgba(255,255,255,0.6)"
CARD_BORDER = "rgba(17,24,39,0.08)"
INK = "#181A24"
MUTED = "#6B7280"
ACCENT_A = "#7C5CFF"
ACCENT_B = "#22D3EE"
GOOD = "#10B981"
WARN = "#F59E0B"
BAD = "#EF4444"

GRADIENT = f"linear-gradient(135deg, {ACCENT_A} 0%, {ACCENT_B} 100%)"


def clean_html(s: str) -> str:
    """Strip leading whitespace from every line.

    Streamlit's Markdown renderer treats 4+ space indentation as a code
    block, which silently breaks `unsafe_allow_html`. HTML doesn't care
    about whitespace between tags, so flattening it is always safe.
    """
    return "\n".join(line.strip() for line in s.strip("\n").split("\n"))


def render(html_str: str) -> None:
    st.markdown(clean_html(html_str), unsafe_allow_html=True)


def inject_css() -> None:
    render(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
    }}
    h1, h2, h3, .gf-heading {{
        font-family: 'Space Grotesk', 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
        color: {INK};
    }}

    .stApp {{
        background: {BG};
        background-image:
            radial-gradient(circle at 15% 0%, rgba(124,92,255,0.10), transparent 45%),
            radial-gradient(circle at 85% 10%, rgba(34,211,238,0.10), transparent 45%);
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{background: transparent;}}

    .block-container {{
        padding-top: 2.2rem;
        max-width: 1100px;
    }}

    /* ---- Sidebar: ~2/3 default width, light glass ---- */
    section[data-testid="stSidebar"] {{
        background: rgba(255,255,255,0.65);
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(17,24,39,0.06);
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        width: 15rem !important;
        min-width: 15rem !important;
        max-width: 15rem !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {INK} !important;
        font-size: 0.86rem;
    }}
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {{
        border-radius: 8px;
        padding: 0.35rem 0.6rem !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {{
        background: rgba(124,92,255,0.10);
    }}

    /* ---- Glass card ---- */
    .gf-card {{
        background: {CARD};
        border: 1px solid {CARD_BORDER};
        backdrop-filter: blur(16px);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 4px 18px rgba(31,41,55,0.05);
        animation: gfFadeUp 0.35s ease both;
    }}
    .gf-card h4, .gf-card h3 {{
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        font-weight: 600;
        color: {INK};
    }}
    .gf-card p {{ color: {MUTED}; font-size: 0.88rem; margin: 0.2rem 0; }}

    @keyframes gfFadeUp {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* ---- Compact top banner ---- */
    .gf-topbar {{ margin-bottom: 1.4rem; }}
    .gf-topbar h1 {{
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        background: {GRADIENT};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .gf-topbar p {{
        color: {MUTED};
        font-size: 0.85rem;
        margin: 0.15rem 0 0 0;
    }}

    /* ---- Stepper ---- */
    .gf-stepper {{ display: flex; gap: 0.4rem; margin-bottom: 1.1rem; flex-wrap: wrap; }}
    .gf-step {{
        display: flex; align-items: center; gap: 0.4rem;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: rgba(17,24,39,0.03);
        border: 1px solid {CARD_BORDER};
        color: {MUTED};
    }}
    .gf-step.active {{
        background: rgba(124,92,255,0.10);
        border-color: rgba(124,92,255,0.4);
        color: {INK};
    }}
    .gf-step .num {{
        width: 16px; height: 16px; border-radius: 50%;
        background: {GRADIENT};
        color: white; font-size: 0.65rem;
        display: flex; align-items: center; justify-content: center;
    }}

    /* ---- Chips: present / missing ---- */
    .gf-chip {{
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 7px;
        font-size: 0.76rem;
        font-weight: 500;
        margin: 0.12rem 0.2rem 0.12rem 0;
    }}
    .gf-chip-present {{ background: rgba(16,185,129,0.12); color: #047857; }}
    .gf-chip-missing {{ background: rgba(239,68,68,0.10); color: #B91C1C; }}
    .gf-chip-neutral {{ background: rgba(124,92,255,0.10); color: #6D28D9; }}

    mark.gf-hit {{
        background: rgba(16,185,129,0.20);
        color: #065F46;
        padding: 0 2px;
        border-radius: 3px;
    }}

    /* ---- Equal-height comparison boxes (section-by-section) ---- */
    .gf-compare-box {{
        height: 280px;
        overflow-y: auto;
    }}

    /* ---- Metric / glass number box ---- */
    .gf-metric {{
        flex: 1; min-width: 130px;
        background: {CARD};
        border: 1px solid {CARD_BORDER};
        backdrop-filter: blur(16px);
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 18px rgba(31,41,55,0.05);
    }}
    .gf-metric .val {{ font-size: 1.7rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }}
    .gf-metric .lab {{ color: {MUTED}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }}
    .gf-metric-row {{ display: flex; gap: 0.7rem; flex-wrap: wrap; margin-bottom: 1rem; }}

    /* ---- Buttons ---- */
    .stButton>button, .stDownloadButton>button {{
        background: {GRADIENT};
        color: white;
        border: none;
        border-radius: 9px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{
        filter: brightness(1.08);
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(124,92,255,0.25);
    }}

    div[data-testid="stVerticalBlock"] > div {{ gap: 0.4rem; }}
    hr {{ border-color: rgba(17,24,39,0.08); margin: 1.4rem 0; }}
    </style>
    """)


def topbar(title: str, subtitle: str) -> None:
    render(f"""
    <div class="gf-topbar">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """)


def stepper(steps: list[str], active_index: int) -> None:
    items = ""
    for i, label in enumerate(steps):
        cls = "gf-step active" if i == active_index else "gf-step"
        items += f'<div class="{cls}"><span class="num">{i+1}</span>{label}</div>'
    render(f'<div class="gf-stepper">{items}</div>')


def chip(text: str, kind: str = "neutral") -> str:
    return f'<span class="gf-chip gf-chip-{kind}">{text}</span>'


def chips(items: list[str], kind: str = "neutral", empty_text: str = "None") -> str:
    if not items:
        return f'<span style="color:{MUTED}; font-size:0.85rem;">{empty_text}</span>'
    return "".join(chip(i, kind) for i in items)


def rating_class(rating: int) -> str:
    if rating >= 8:
        return "good"
    if rating >= 5:
        return "warn"
    return "bad"


def rating_color(rating: int) -> str:
    return {"good": GOOD, "warn": WARN, "bad": BAD}[rating_class(rating)]


def donut(rating: int, size: int = 84, max_value: int = 10) -> str:
    """A donut ring with the rating shown large in the center hole.

    rating/max_value determines how much of the ring is filled, colored
    green/orange/red by the same thresholds used everywhere else.
    """
    pct = max(0, min(max_value, rating)) / max_value * 100
    color = rating_color(round(rating / max_value * 10))
    hole = size - 16
    font_size = round(size * 0.30)
    sub_size = round(size * 0.13)
    return f"""
    <div style="position:relative; width:{size}px; height:{size}px; border-radius:50%; flex-shrink:0;
        background: conic-gradient({color} {pct}%, rgba(17,24,39,0.08) {pct}% 100%);
        display:flex; align-items:center; justify-content:center;">
        <div style="width:{hole}px; height:{hole}px; border-radius:50%; background:{SURFACE};
            display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <span style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:{font_size}px; color:{color}; line-height:1;">{rating}</span>
            <span style="font-size:{sub_size}px; color:{MUTED};">/ {max_value}</span>
        </div>
    </div>
    """


def metric_box(label: str, value, color: str = ACCENT_A) -> str:
    return f"""
    <div class="gf-metric">
        <div class="val" style="color:{color};">{value}</div>
        <div class="lab">{label}</div>
    </div>
    """


def metric_row(boxes_html: list[str]) -> None:
    render(f'<div class="gf-metric-row">{"".join(boxes_html)}</div>')
