import streamlit as st

from utils.styling import inject_css, hero, score_box, pill
from utils.state import init_state
from utils.parsers import parse_resume
from utils.job_intel import fetch_job_from_url, build_job_listing_from_text, extract_keywords
from utils.ats_scorer import run_full_analysis
from utils.ai_client import semantic_gap_analysis, section_feedback, rewrite_bullets_star
from utils.exporter import text_to_docx, text_to_pdf

st.set_page_config(page_title="Resume Optimizer • ResumeForge AI", page_icon="📄", layout="wide")
inject_css()
init_state()
hero("📄 Resume Optimizer", "Upload your resume, target a job, and see exactly what to fix before you apply.")

# --- Step 1: Upload resume ----------------------------------------------------
st.markdown("### Step 1 — Import your resume")
uploaded = st.file_uploader("Upload baseline resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded is not None:
    file_bytes = uploaded.read()
    if uploaded.name != st.session_state.get("resume_filename"):
        with st.spinner("Reading your resume..."):
            try:
                parsed = parse_resume(file_bytes, uploaded.name)
                st.session_state.resume_bytes = file_bytes
                st.session_state.resume_filename = uploaded.name
                st.session_state.parsed_resume = parsed
                # reset downstream state since resume changed
                st.session_state.analytics_before = None
                st.session_state.gap_analysis = None
                st.session_state.section_feedback = None
                st.session_state.rewritten_bullets = None
            except ValueError as e:
                st.error(str(e))

if st.session_state.parsed_resume:
    st.success(f"✅ Loaded: {st.session_state.resume_filename} ({len(st.session_state.parsed_resume.raw_text.split())} words)")
    with st.expander("Preview extracted text"):
        st.text(st.session_state.parsed_resume.raw_text[:3000])

st.divider()

# --- Step 2: Job info ---------------------------------------------------------
st.markdown("### Step 2 — Auto-extract job info")
tab_url, tab_text = st.tabs(["🔗 Paste job URL", "📋 Paste job text"])

with tab_url:
    url = st.text_input("Job listing URL")
    if st.button("Fetch job from URL", key="fetch_url_btn"):
        with st.spinner("Fetching listing..."):
            try:
                listing = fetch_job_from_url(url)
                st.session_state.job_listing = listing
                st.session_state.job_keywords = extract_keywords(listing.raw_text)
                st.success("Job description fetched.")
            except ValueError as e:
                st.error(str(e))

with tab_text:
    company_name = st.text_input("Company name (optional)", key="company_input")
    job_title_input = st.text_input("Job title (optional)", key="title_input")
    job_text_input = st.text_area("Paste the full job description", height=220)
    if st.button("Use this job description", key="use_text_btn"):
        listing = build_job_listing_from_text(job_text_input, title=job_title_input, company=company_name)
        st.session_state.job_listing = listing
        st.session_state.job_keywords = extract_keywords(job_text_input)
        st.success("Job description saved.")

if st.session_state.job_listing and st.session_state.job_listing.raw_text:
    with st.expander("Preview job description"):
        st.text(st.session_state.job_listing.raw_text[:2500])
    st.caption(f"Extracted {len(st.session_state.job_keywords)} candidate keywords for ATS matching.")

st.divider()

# --- Step 3: Run analysis ------------------------------------------------------
st.markdown("### Step 3 — ATS Score Comparison")

ready = st.session_state.parsed_resume is not None
run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button("🔍 Run ATS Analysis", disabled=not ready, use_container_width=True)

if not ready:
    st.info("Upload a resume above to run analysis.")

if run_clicked:
    with st.spinner("Scoring your resume..."):
        before = run_full_analysis(
            st.session_state.parsed_resume,
            st.session_state.resume_filename,
            job_keywords=st.session_state.job_keywords,
        )
        st.session_state.analytics_before = before

    if st.session_state.job_listing and st.session_state.job_listing.raw_text:
        with st.spinner("Running semantic gap analysis with AI..."):
            try:
                st.session_state.gap_analysis = semantic_gap_analysis(
                    st.session_state.parsed_resume.raw_text,
                    st.session_state.job_listing.raw_text,
                )
            except Exception as e:
                st.warning(f"Gap analysis unavailable: {e}")

        with st.spinner("Generating section-wise feedback..."):
            try:
                st.session_state.section_feedback = section_feedback(
                    st.session_state.parsed_resume.raw_text,
                    st.session_state.job_listing.raw_text,
                )
            except Exception as e:
                st.warning(f"Section feedback unavailable: {e}")

if st.session_state.analytics_before:
    before = st.session_state.analytics_before
    # "Modified" score is illustrative: current score + potential lift if
    # missing keywords/quant points get addressed via the STAR rewriter below.
    potential_lift = min(25, len(before.missing_keywords) * 2 + (10 if before.quantified_bullet_ratio < 0.5 else 0))
    after_estimate = min(100, before.overall_score + potential_lift)

    st.markdown(
        f"""<div class="rf-score-wrap">
        {score_box("Current ATS Score", before.overall_score, "#FF6B6B" if before.overall_score < 60 else "#FDCB6E" if before.overall_score < 80 else "#00B894")}
        {score_box("Potential Score After Fixes", after_estimate, "#00B894")}
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption("Potential score reflects applying the keyword and quantification fixes suggested below — head to Advanced Analytics for the full breakdown.")

st.divider()

# --- Step 4: Semantic Gap Analysis --------------------------------------------
if st.session_state.gap_analysis:
    st.markdown("### Semantic Gap Analysis & Compatibility Strategy")
    gap = st.session_state.gap_analysis

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(
            f"""<div class="rf-card"><h3>Alignment Score</h3>
            <div class="rf-score-num" style="color:#6C5CE7;">{gap.get('alignment_score_0_to_100', '—')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f"""<div class="rf-card"><h3>Summary</h3><p>{gap.get('compatibility_summary', '')}</p></div>""", unsafe_allow_html=True)

    kw_col1, kw_col2, kw_col3 = st.columns(3)
    with kw_col1:
        st.markdown("**Missing Keywords**")
        st.markdown("".join(pill(k, "bad") for k in gap.get("missing_keywords", [])) or "None 🎉", unsafe_allow_html=True)
    with kw_col2:
        st.markdown("**Missing Technical Skills**")
        st.markdown("".join(pill(k, "warn") for k in gap.get("missing_technical_skills", [])) or "None 🎉", unsafe_allow_html=True)
    with kw_col3:
        st.markdown("**Missing Industry Terms**")
        st.markdown("".join(pill(k, "neutral") for k in gap.get("missing_industry_terms", [])) or "None 🎉", unsafe_allow_html=True)

    st.markdown("**Alignment Strategy**")
    for item in gap.get("alignment_strategy", []):
        st.markdown(f"- {item}")

st.divider()

# --- Step 5: Section-wise pros & cons -----------------------------------------
if st.session_state.section_feedback:
    st.markdown("### Section-wise Pros & Cons")
    sf = st.session_state.section_feedback
    cols = st.columns(4)
    for col, section in zip(cols, ["summary", "experience", "projects", "skills"]):
        data = sf.get(section, {})
        with col:
            st.markdown(f"""<div class="rf-card"><h3>{section.title()}</h3>""", unsafe_allow_html=True)
            for pro in data.get("pros", []):
                st.markdown(f"✅ {pro}")
            for con in data.get("cons", []):
                st.markdown(f"⚠️ {con}")
            st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- Step 6: STAR bullet rewriting + side-by-side view ------------------------
st.markdown("### STAR-Method Bullet Optimizer")
st.caption("Paste (or edit) the experience bullets you want rewritten. One bullet per line.")

default_bullets = ""
if st.session_state.parsed_resume and st.session_state.parsed_resume.sections.get("experience"):
    default_bullets = st.session_state.parsed_resume.sections["experience"][:1500]

bullets_input = st.text_area("Experience bullets", value=default_bullets, height=180, key="bullets_area")

if st.button("✨ Rewrite bullets with STAR method"):
    lines = [b.strip("•-* \t") for b in bullets_input.split("\n") if len(b.strip()) > 5]
    if not lines:
        st.warning("Add at least one bullet point first.")
    else:
        with st.spinner("Rewriting bullets..."):
            try:
                job_text = st.session_state.job_listing.raw_text if st.session_state.job_listing else ""
                st.session_state.rewritten_bullets = rewrite_bullets_star(lines, job_text)
            except Exception as e:
                st.error(f"Couldn't rewrite bullets: {e}")

if st.session_state.rewritten_bullets:
    st.markdown("#### Side-by-Side: Original vs AI-Suggested")
    for i, item in enumerate(st.session_state.rewritten_bullets):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="rf-card"><b>Original</b><p>{item.get('original','')}</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"""<div class="rf-card" style="border-color:#00CEC9;"><b>AI-Suggested</b>
                <p>{item.get('rewritten','')}</p>
                <p style="color:#6B7280; font-size:0.85rem;">💡 {item.get('note','')}</p></div>""",
                unsafe_allow_html=True,
            )

st.divider()

# --- Step 7: Export ------------------------------------------------------------
st.markdown("### ATS-Friendly Export")
export_source = st.radio("What do you want to export?", ["Original resume text", "Rewritten bullets appended to resume"], horizontal=True)

if st.session_state.parsed_resume:
    if export_source == "Original resume text":
        final_text = st.session_state.parsed_resume.raw_text
    else:
        rewritten_block = "\n".join(
            f"• {item.get('rewritten','')}" for item in (st.session_state.rewritten_bullets or [])
        )
        final_text = st.session_state.parsed_resume.raw_text + "\n\n--- OPTIMIZED BULLETS ---\n" + rewritten_block

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "⬇️ Download as DOCX",
            data=text_to_docx("Resume", final_text),
            file_name="optimized_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "⬇️ Download as PDF",
            data=text_to_pdf("Resume", final_text),
            file_name="optimized_resume.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
else:
    st.info("Upload a resume to enable export.")
