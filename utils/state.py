"""Central place for session_state defaults.

IMPORTANT: Streamlit runs whichever page the user lands on — if someone
opens a page link directly (or refreshes one), app.py may never execute
in that session. So every page must call init_state() itself, first
thing, rather than relying on app.py having already set these keys.
"""

import streamlit as st

_DEFAULTS = {
    "resume_filename": None,
    "resume_bytes": None,
    "parsed_resume": None,       # utils.parsers.ParsedResume
    "job_listing": None,         # utils.job_intel.JobListing
    "job_keywords": [],
    "analytics_before": None,    # utils.ats_scorer.AnalyticsReport
    "analytics_after": None,
    "gap_analysis": None,
    "section_feedback": None,
    "rewritten_bullets": None,
    "cover_letter_text": None,
    "salary_estimate": None,
}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
