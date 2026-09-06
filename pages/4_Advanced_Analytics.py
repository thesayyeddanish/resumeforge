import streamlit as st

from utils.styling import inject_css, hero, score_box, pill
from utils.ats_scorer import run_full_analysis

st.set_page_config(page_title="Advanced Analytics • ResumeForge AI", page_icon="📊", layout="wide")
inject_css()
hero("📊 Advanced Analytics", "A full diagnostic pass on your resume — the same checks recruiters' ATS systems run before a human ever sees it.")

if not st.session_state.get("parsed_resume"):
    st.warning("Upload a resume on the **Resume Optimizer** page first.")
    st.stop()

# Recompute fresh each visit so it reflects the latest job keywords too
report = run_full_analysis(
    st.session_state.parsed_resume,
    st.session_state.resume_filename,
    job_keywords=st.session_state.get("job_keywords", []),
)
st.session_state.analytics_before = report

score_color = "#FF6B6B" if report.overall_score < 60 else "#FDCB6E" if report.overall_score < 80 else "#00B894"
st.markdown(
    f"""<div class="rf-score-wrap">{score_box("Overall Resume Score", report.overall_score, score_color)}</div>""",
    unsafe_allow_html=True,
)
st.caption("This score reflects your resume BEFORE optimization. Run the Resume Optimizer to see improvement potential.")

st.divider()

STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
STATUS_PILL = {"pass": "good", "warn": "warn", "fail": "bad"}

st.markdown("### Detailed Checklist")

for i, check in enumerate(report.checks, start=1):
    icon = STATUS_ICON[check.status]
    with st.container():
        st.markdown(
            f"""<div class="rf-card">
            <div class="rf-check-row">
                <div><b>{i}. {check.name}</b></div>
                <div>{icon} {pill(check.status.upper(), STATUS_PILL[check.status])}</div>
            </div>
            <p style="margin-top:0.5rem; color:#374151;">{check.detail}</p>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

st.markdown("### Matching & Missing Keywords")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**✅ Matched Keywords**")
    st.markdown("".join(pill(k, "good") for k in report.matched_keywords) or "_No job description loaded yet._", unsafe_allow_html=True)
with c2:
    st.markdown("**❌ Missing Keywords**")
    st.markdown("".join(pill(k, "bad") for k in report.missing_keywords) or "_No job description loaded yet, or nothing missing 🎉_", unsafe_allow_html=True)

st.divider()
st.markdown("### Quantified Bullet Ratio")
st.progress(min(report.quantified_bullet_ratio, 1.0))
st.caption(f"{report.quantified_bullet_ratio:.0%} of your experience bullets contain a number, %, or $ metric. Aim for 50%+.")
