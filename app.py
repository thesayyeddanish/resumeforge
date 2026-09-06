import streamlit as st

from utils.styling import inject_css, hero

st.set_page_config(
    page_title="ResumeForge AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# --- Global session state (shared across all pages) -------------------------
defaults = {
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
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

hero(
    "🧠 ResumeForge AI",
    "Your all-in-one job application co-pilot — ATS scoring, semantic gap analysis, "
    "STAR bullet rewriting, cover letters, and salary intel in one place.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        """<div class="rf-card"><h3>📄 Resume Optimizer</h3>
        <p>Upload your resume, paste a job listing, and get before/after ATS scores
        with a full advanced analytics breakdown.</p></div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        """<div class="rf-card"><h3>✉️ Cover Letter</h3>
        <p>Generate a tailored, 3-paragraph cover letter that matches the
        target company's tone — grounded only in your real experience.</p></div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        """<div class="rf-card"><h3>💰 Salary Estimator</h3>
        <p>Get a modeled salary range for a target company and title,
        with a clear confidence level and reasoning.</p></div>""",
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        """<div class="rf-card"><h3>📊 Advanced Analytics</h3>
        <p>Deep-dive resume health check: contact info, grammar, pronoun usage,
        keyword targeting, sentence complexity, and more.</p></div>""",
        unsafe_allow_html=True,
    )

st.markdown("### 🚀 Get started")
st.markdown(
    """<div class="rf-card">
    <p>Use the sidebar to navigate:</p>
    <ol>
        <li>Go to <b>Resume Optimizer</b> and upload your resume (PDF/DOCX) + paste or link the job.</li>
        <li>Review your <b>Advanced Analytics</b> breakdown and semantic gap analysis.</li>
        <li>Accept AI-suggested STAR rewrites in the side-by-side view.</li>
        <li>Generate your <b>Cover Letter</b> and check the <b>Salary Estimator</b>.</li>
        <li>Export your final, ATS-friendly resume and cover letter as PDF or DOCX.</li>
    </ol>
    <p style="color:#6B7280; font-size:0.9rem;">🔒 Truth Guardrail is always on: the AI only rephrases
    your real experience — it never invents skills, degrees, or jobs.</p>
    </div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🧠 ResumeForge AI")
    st.caption("Navigate using the pages above.")
    st.divider()
    if st.session_state.resume_filename:
        st.success(f"Resume loaded: {st.session_state.resume_filename}")
    else:
        st.info("No resume uploaded yet.")
    if st.session_state.job_listing and st.session_state.job_listing.raw_text:
        st.success("Job description loaded.")
    else:
        st.info("No job description loaded yet.")
