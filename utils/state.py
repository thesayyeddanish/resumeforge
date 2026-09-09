"""Central place for session_state defaults.

IMPORTANT: Streamlit runs whichever page the user lands on -- if someone
opens a page link directly (or refreshes one), Home.py may never execute
in that session. So every page must call init_state() itself, first
thing, rather than relying on Home.py having already set these keys.
"""

import streamlit as st

_DEFAULTS = {
    "resume_filename": None,
    "resume_bytes": None,
    "parsed_resume": None,       # utils.parsers.ParsedResume
    "job_listing": None,         # utils.job_intel.JobListing
    "job_keywords": [],
    "analytics_before": None,    # utils.ats_scorer.AnalyticsReport
    "gap_analysis": None,
    "section_feedback": None,
    "weak_bullet_rewrites": None,   # per-bullet quick suggestions (separate from the full rewrite below)
    "optimized_resume_text": None,  # full-resume rewrite that drives the Export "Modified" column
    "optimize_resume_error": None,  # persisted so it doesn't vanish on the next unrelated rerun
    "optimize_status": None,        # always-set outcome summary (success/no-op/failure) for diagnosis
    "cover_letter_text": None,
    "cover_letter_cache_key": None,
    "salary_estimate": None,
}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
