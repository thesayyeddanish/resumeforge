import streamlit as st

from utils.styling import inject_css, render
from utils.state import init_state

st.set_page_config(
    page_title="ResumeForge AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_state()

# --- Compact header (no giant hero banner) -----------------------------------
render("""
<div style="margin-bottom:1.1rem;">
    <div style="display:flex; align-items:center; gap:0.5rem;">
        <span style="font-size:1.5rem;">🧠</span>
        <span style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.35rem;
            background:linear-gradient(135deg,#7C5CFF,#22D3EE); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            ResumeForge AI
        </span>
    </div>
    <p style="color:#8B90A0; font-size:0.88rem; margin:0.25rem 0 0 2rem;">
        Your job application co-pilot — ATS scoring, gap analysis, bullet rewriting, cover letters, and salary intel.
    </p>
</div>
""")

# --- Feature grid: everything visible in the first screen ---------------------
features = [
    ("📄", "Resume Optimizer", "Upload your resume, target a job, and see exactly what to fix."),
    ("✉️", "Cover Letter", "A tailored, tone-matched letter generated from your real experience."),
    ("💰", "Salary Estimator", "A modeled compensation range for a target company and role."),
    ("📊", "Advanced Analytics", "A full diagnostic pass, rated section by section."),
]

cols = st.columns(4)
for col, (icon, title, desc) in zip(cols, features):
    with col:
        render(f"""
        <div class="gf-card" style="min-height:150px;">
            <div style="font-size:1.3rem;">{icon}</div>
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>
        """)

render("""
<div class="gf-card" style="margin-top:0.3rem; border-color:rgba(124,92,255,0.35);">
    <p style="color:#B8A9FF; font-size:0.85rem; margin:0;">
        🔒 <b>Truth Guardrail</b> is always on — the AI only rephrases your real experience.
        It never invents skills, degrees, or jobs. Start with <b>Resume Optimizer</b> in the sidebar →
    </p>
</div>
""")

st.divider()

# --- Below the fold: how it works ---------------------------------------------
render("""<h3 class="gf-heading" style="font-size:1.05rem; margin-bottom:0.8rem;">How it works</h3>""")

steps = [
    ("1", "Resume Optimizer", "Upload your resume (PDF/DOCX) and paste or link the target job. Get before/after ATS scores, a keyword gap analysis, and bullet-by-bullet rewrite suggestions — all side by side with your original text."),
    ("2", "Cover Letter", "Once a job is loaded, a matching 3-paragraph cover letter is ready automatically — edit, copy, or download it."),
    ("3", "Salary Estimator", "Enter a title, company, and location to get a modeled compensation range with reasoning."),
    ("4", "Advanced Analytics", "A deeper diagnostic: contact info, grammar, pronoun usage, keyword coverage, sentence complexity, and quantification — each rated out of 10 with specific, actionable feedback."),
]

for num, title, desc in steps:
    render(f"""
    <div class="gf-card" style="display:flex; gap:0.9rem; align-items:flex-start;">
        <div style="min-width:28px; height:28px; border-radius:8px; background:linear-gradient(135deg,#7C5CFF,#22D3EE);
            display:flex; align-items:center; justify-content:center; font-weight:700; color:white; font-size:0.85rem;">{num}</div>
        <div>
            <h4 style="margin-bottom:0.15rem;">{title}</h4>
            <p style="margin:0;">{desc}</p>
        </div>
    </div>
    """)

with st.sidebar:
    render('<div style="font-family:\'Space Grotesk\',sans-serif; font-weight:700; padding:0.4rem 0;">🧠 ResumeForge AI</div>')
    st.divider()
    if st.session_state.resume_filename:
        st.success(f"Resume: {st.session_state.resume_filename}", icon="✅")
    else:
        st.caption("No resume uploaded yet.")
    if st.session_state.job_listing and st.session_state.job_listing.raw_text:
        st.success("Job description loaded.", icon="✅")
    else:
        st.caption("No job description yet.")
