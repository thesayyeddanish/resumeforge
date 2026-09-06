import streamlit as st

from utils.styling import inject_css, hero, score_box
from utils.ai_client import estimate_salary

st.set_page_config(page_title="Salary Estimator • ResumeForge AI", page_icon="💰", layout="wide")
inject_css()
hero("💰 Salary Range Estimator", "A modeled estimate based on role, company, and location — always verify against live market data before negotiating.")

c1, c2 = st.columns(2)
with c1:
    job_title = st.text_input("Target job title", placeholder="e.g. Senior Product Manager")
    location = st.text_input("Location", placeholder="e.g. Bangalore, India / Remote-US")
with c2:
    company = st.text_input("Company name", placeholder="e.g. Google, or a startup name")
    years_exp = st.text_input("Years of experience", placeholder="e.g. 5")

if st.button("💰 Estimate Salary Range", use_container_width=False):
    if not job_title.strip():
        st.warning("Enter at least a job title.")
    else:
        with st.spinner("Modeling a salary range..."):
            try:
                st.session_state.salary_estimate = estimate_salary(job_title, company, location, years_exp)
            except Exception as e:
                st.error(f"Couldn't estimate salary: {e}")

if st.session_state.get("salary_estimate"):
    est = st.session_state.salary_estimate
    st.markdown(
        f"""<div class="rf-score-wrap">
        {score_box("Low", est.get('low_estimate','—'), "#FF6B6B")}
        {score_box("Mid", est.get('mid_estimate','—'), "#6C5CE7")}
        {score_box("High", est.get('high_estimate','—'), "#00B894")}
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(f"""<div class="rf-card"><h3>Reasoning</h3><p>{est.get('reasoning','')}</p>
    <p><b>Confidence:</b> {est.get('confidence','—').title()}</p>
    <p style="color:#6B7280; font-size:0.85rem;">{est.get('currency_note','')}</p>
    </div>""", unsafe_allow_html=True)
    st.warning(f"⚠️ {est.get('disclaimer', 'This is a modeled estimate, not live market data.')}")
    st.caption("For live data, cross-check with Levels.fyi, Glassdoor, Payscale, or Blind before negotiating.")
