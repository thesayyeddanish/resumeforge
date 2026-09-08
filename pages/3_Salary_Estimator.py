import streamlit as st

from utils.styling import inject_css, topbar, render, metric_box, metric_row, GOOD, WARN, BAD, ACCENT_A
from utils.state import init_state
from utils.ai_client import estimate_salary

st.set_page_config(page_title="Salary Estimator • ResumeForge AI", page_icon="💰", layout="wide")
inject_css()
init_state()

topbar("💰 Salary Estimator", "A modeled range based on role, company, and location — always verify against live market data.")

c1, c2 = st.columns(2)
with c1:
    job_title = st.text_input("Job title", placeholder="e.g. Senior Product Manager")
    location = st.text_input("Location", placeholder="e.g. Bangalore, India / Remote-US")
with c2:
    company = st.text_input("Company", placeholder="e.g. Google, or a startup name")
    years_exp = st.text_input("Years of experience", placeholder="e.g. 5")

if st.button("Estimate", type="primary"):
    if not job_title.strip():
        st.warning("Enter at least a job title.")
    else:
        with st.spinner("Modeling a range..."):
            try:
                st.session_state.salary_estimate = estimate_salary(job_title, company, location, years_exp)
            except Exception as e:
                st.error(f"Couldn't estimate salary: {e}")

est = st.session_state.get("salary_estimate")
if est:
    metric_row([
        metric_box("Low", est.get("low_estimate", "—"), BAD),
        metric_box("Mid", est.get("mid_estimate", "—"), ACCENT_A),
        metric_box("High", est.get("high_estimate", "—"), GOOD),
    ])

    conf = (est.get("confidence") or "—").title()
    conf_color = {"High": GOOD, "Medium": WARN, "Low": BAD}.get(conf, ACCENT_A)

    render(f"""
    <div class="gf-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <h4 style="margin:0;">Reasoning</h4>
            <span style="font-size:0.75rem; padding:0.2rem 0.6rem; border-radius:999px; background:rgba(255,255,255,0.06); color:{conf_color};">
                {conf} confidence
            </span>
        </div>
        <p>{est.get('reasoning','')}</p>
        <p style="font-size:0.78rem; opacity:0.7;">{est.get('currency_note','')}</p>
    </div>
    """)
    st.warning(f"⚠️ {est.get('disclaimer', 'This is a modeled estimate, not live market data.')}")
    st.caption("For live data, cross-check with Levels.fyi, Glassdoor, Payscale, or Blind before negotiating.")
