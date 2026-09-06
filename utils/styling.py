"""Shared visual styling for ResumeForge AI.

Import `inject_css()` at the top of every page so the whole app feels
like one product instead of separate Streamlit pages bolted together.
"""

import streamlit as st


PRIMARY = "#6C5CE7"
PRIMARY_DARK = "#4834d4"
ACCENT = "#00CEC9"
SUCCESS = "#00B894"
WARNING = "#FDCB6E"
DANGER = "#FF6B6B"
INK = "#1E1E2E"
MUTED = "#6B7280"
CARD_BG = "#FFFFFF"
PAGE_BG = "#F7F7FC"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background: {PAGE_BG};
        }}

        /* Hide default Streamlit chrome for a more "product" feel */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{background: transparent;}}

        /* Hero / page header */
        .rf-hero {{
            background: linear-gradient(120deg, {PRIMARY} 0%, {PRIMARY_DARK} 60%, {ACCENT} 130%);
            padding: 2.2rem 2.4rem;
            border-radius: 20px;
            color: white;
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 30px rgba(108, 92, 231, 0.25);
        }}
        .rf-hero h1 {{
            margin: 0;
            font-weight: 800;
            font-size: 2rem;
            letter-spacing: -0.02em;
        }}
        .rf-hero p {{
            margin: 0.4rem 0 0 0;
            opacity: 0.92;
            font-size: 1.02rem;
        }}

        /* Card container */
        .rf-card {{
            background: {CARD_BG};
            border: 1px solid #ECECF6;
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            box-shadow: 0 2px 10px rgba(30, 30, 46, 0.04);
            margin-bottom: 1rem;
        }}
        .rf-card h3 {{
            margin-top: 0;
            font-weight: 700;
            color: {INK};
        }}

        /* Score badge */
        .rf-score-wrap {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        .rf-score-box {{
            flex: 1;
            min-width: 160px;
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
            background: {CARD_BG};
            border: 1px solid #ECECF6;
        }}
        .rf-score-num {{
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1;
        }}
        .rf-score-label {{
            color: {MUTED};
            font-size: 0.85rem;
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        /* Pill / tag */
        .rf-pill {{
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 0.15rem 0.25rem 0.15rem 0;
        }}
        .rf-pill-good {{ background: rgba(0,184,148,0.12); color: {SUCCESS}; }}
        .rf-pill-bad {{ background: rgba(255,107,107,0.12); color: {DANGER}; }}
        .rf-pill-warn {{ background: rgba(253,203,110,0.20); color: #9C6B00; }}
        .rf-pill-neutral {{ background: rgba(108,92,231,0.10); color: {PRIMARY_DARK}; }}

        /* Section status row */
        .rf-check-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0;
            border-bottom: 1px solid #F0F0F7;
        }}
        .rf-check-row:last-child {{ border-bottom: none; }}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(120deg, {PRIMARY}, {PRIMARY_DARK});
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.55rem 1.4rem;
            font-weight: 600;
            transition: all 0.15s ease;
        }}
        .stButton>button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(108, 92, 231, 0.35);
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: #14142B;
        }}
        section[data-testid="stSidebar"] * {{
            color: #EDEDF7 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="rf-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_box(label: str, value: int, color: str = PRIMARY) -> str:
    return f"""
        <div class="rf-score-box">
            <div class="rf-score-num" style="color:{color};">{value}</div>
            <div class="rf-score-label">{label}</div>
        </div>
    """


def pill(text: str, kind: str = "neutral") -> str:
    return f'<span class="rf-pill rf-pill-{kind}">{text}</span>'
