import streamlit as st

from utils.styling import inject_css, topbar, render, chips, rating_badge, rating_color, metric_box, metric_row
from utils.state import init_state
from utils.ats_scorer import run_full_analysis

st.set_page_config(page_title="Advanced Analytics • ResumeForge AI", page_icon="📊", layout="wide")
inject_css()
init_state()

topbar("📊 Advanced Analytics", "A full diagnostic pass — the same checks recruiters' ATS systems run before a human sees it.")

if not st.session_state.get("parsed_resume"):
    st.warning("Upload a resume on the Resume Optimizer page first.")
    st.stop()

report = run_full_analysis(
    st.session_state.parsed_resume, st.session_state.resume_filename, job_keywords=st.session_state.get("job_keywords", []),
)
st.session_state.analytics_before = report

score_color = rating_color(round(report.overall_score / 10))
metric_row([metric_box("Overall Resume Score", report.overall_score, score_color)])
st.caption("This reflects your resume BEFORE optimization. Fix the lowest-rated items below for the biggest lift.")

st.divider()


def check_card(title: str, body_html: str) -> None:
    check = next(c for c in report.checks if c.name == title)
    render(f"""
    <div class="gf-card" style="display:flex; gap:0.9rem;">
        {rating_badge(check.rating)}
        <div style="flex:1;">
            <div style="display:flex; justify-content:space-between; align-items:baseline;">
                <h4 style="margin:0;">{title}</h4>
                <span style="color:#8B90A0; font-size:0.78rem;">{check.rating}/10</span>
            </div>
            <p style="margin:0.15rem 0 0.5rem 0;">{check.summary}</p>
            {body_html}
        </div>
    </div>
    """)


# 1. Contact Information
contact = next(c for c in report.checks if c.name == "Contact Information")
field_rows = "".join(
    f'<span style="margin-right:1rem; font-size:0.85rem;">{"✅" if present else "❌"} {field}</span>'
    for field, present in contact.data["fields"].items()
)
check_card("Contact Information", f"<div>{field_rows}</div>")

# 2. Spelling & Grammar
spelling = next(c for c in report.checks if c.name == "Spelling & Grammar")
if spelling.data["misspelled"]:
    body = chips(spelling.data["misspelled"], "missing")
else:
    body = '<p style="color:#34D399;">No flagged words 🎉</p>'
check_card("Spelling & Grammar", body)

# 3. Personal Pronoun Usage
pronoun = next(c for c in report.checks if c.name == "Personal Pronoun Usage")
if pronoun.data["examples"]:
    body = "".join(f'<p style="font-style:italic; font-size:0.82rem;">"{ex}"</p>' for ex in pronoun.data["examples"])
else:
    body = '<p style="color:#34D399;">No first-person pronouns found 🎉</p>'
check_card("Personal Pronoun Usage", body)

# 4. Skills & Keyword Targeting
kw = next(c for c in report.checks if c.name == "Skills & Keyword Targeting")
render(f"""
<div class="gf-card" style="display:flex; gap:0.9rem;">
    {rating_badge(kw.rating)}
    <div style="flex:1;">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <h4 style="margin:0;">Skills & Keyword Targeting</h4>
            <span style="color:#8B90A0; font-size:0.78rem;">{kw.rating}/10</span>
        </div>
        <p style="margin:0.15rem 0 0.5rem 0;">{kw.summary}</p>
    </div>
</div>
""")
pc, mc = st.columns(2)
with pc:
    render(chips(kw.data.get("matched", []), "present", "None found"))
with mc:
    render(chips(kw.data.get("missing", []), "missing", "None missing 🎉"))

# 5. Sentence Complexity
complexity = next(c for c in report.checks if c.name == "Sentence Complexity")
note = "Looks good — clear and scannable." if complexity.rating >= 7 else "Consider shortening some sentences for an easier recruiter scan."
check_card("Sentence Complexity", f'<p>{note}</p>')

# 6. Quantified Achievements
quant = next(c for c in report.checks if c.name == "Quantified Achievements")
target_pct = int(quant.data.get("target_ratio", 0.5) * 100)
weak = quant.data.get("weak_bullets", [])
if weak:
    body = f'<p style="font-size:0.82rem;">Aim for {target_pct}%+ of bullets with a number. These currently have none:</p>' + \
           "".join(f'<p style="font-size:0.82rem; padding:0.3rem 0.5rem; background:rgba(248,113,113,0.08); border-radius:6px; margin:0.25rem 0;">{b}</p>' for b in weak)
else:
    body = '<p style="color:#34D399;">All bullets are quantified 🎉</p>'
check_card("Quantified Achievements", body)

# 7. Essential Resume Sections
sections = next(c for c in report.checks if c.name == "Essential Resume Sections")
found_html = "".join(f'<span style="margin-right:1rem; font-size:0.85rem;">✅ {s.title()}</span>' for s in sections.data["found"])
missing_html = "".join(f'<span style="margin-right:1rem; font-size:0.85rem;">❌ {s.title()}</span>' for s in sections.data["missing"])
check_card("Essential Resume Sections", f"<div>{found_html}{missing_html}</div>")

# 8. Document Properties
docprops = next(c for c in report.checks if c.name == "Document Properties")
if docprops.data["issues"]:
    body = "".join(f'<p style="font-size:0.82rem;">• {issue}</p>' for issue in docprops.data["issues"])
else:
    body = '<p style="color:#34D399;">No structural red flags 🎉</p>'
check_card("Document Properties", body)

st.divider()

# --- Meaningful closing section: priority action plan, not raw data dumps ---
render('<h4 class="gf-heading">Priority Action Plan</h4>')
weakest = sorted(report.checks, key=lambda c: c.rating)[:3]
for i, c in enumerate(weakest, start=1):
    render(f"""
    <div class="gf-card" style="display:flex; gap:0.9rem;">
        <div style="min-width:26px; height:26px; border-radius:8px; background:linear-gradient(135deg,#7C5CFF,#22D3EE);
            display:flex; align-items:center; justify-content:center; font-weight:700; color:white; font-size:0.8rem;">{i}</div>
        <div>
            <h4 style="margin-bottom:0.1rem;">{c.name} <span style="color:#8B90A0; font-weight:400; font-size:0.8rem;">({c.rating}/10)</span></h4>
            <p style="margin:0;">{c.summary}</p>
        </div>
    </div>
    """)
