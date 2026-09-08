import streamlit as st

from utils.styling import inject_css, topbar, stepper, render, chips, metric_box, metric_row, ACCENT_A, GOOD, WARN, BAD
from utils.state import init_state
from utils.parsers import parse_resume
from utils.job_intel import fetch_job_from_url, build_job_listing_from_text, extract_keywords
from utils.ats_scorer import run_full_analysis
from utils.ai_client import semantic_gap_analysis, section_feedback, rewrite_bullets
from utils.highlight import highlight_matches
from utils.exporter import text_to_docx, text_to_pdf, apply_bullet_replacements_to_docx

st.set_page_config(page_title="Resume Optimizer • ResumeForge AI", page_icon="📄", layout="wide")
inject_css()
init_state()

topbar("📄 Resume Optimizer", "Upload a resume, target a job, and see exactly what to fix before you apply.")

# Figure out which step is "active" for the stepper display
has_resume = st.session_state.parsed_resume is not None
has_job = bool(st.session_state.job_listing and st.session_state.job_listing.raw_text)
has_analysis = st.session_state.analytics_before is not None
active = 3 if has_analysis else 2 if has_job else 1 if has_resume else 0
stepper(["Upload resume", "Add target job", "Run analysis", "Review & export"], active)

# ============================================================================
# STEP 1 — Upload
# ============================================================================
c1, c2 = st.columns([2, 1])
with c1:
    uploaded = st.file_uploader("Upload resume", type=["pdf", "docx"], label_visibility="collapsed",
                                 help="PDF or DOCX")
with c2:
    if st.session_state.parsed_resume:
        render(f'<div style="padding-top:0.4rem; color:{GOOD}; font-size:0.85rem;">✓ {st.session_state.resume_filename} · {len(st.session_state.parsed_resume.raw_text.split())} words</div>')

if uploaded is not None:
    file_bytes = uploaded.read()
    if uploaded.name != st.session_state.get("resume_filename"):
        with st.spinner("Reading resume..."):
            try:
                parsed = parse_resume(file_bytes, uploaded.name)
                st.session_state.resume_bytes = file_bytes
                st.session_state.resume_filename = uploaded.name
                st.session_state.parsed_resume = parsed
                st.session_state.analytics_before = None
                st.session_state.gap_analysis = None
                st.session_state.section_feedback = None
                st.session_state.weak_bullet_rewrites = None
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()

# ============================================================================
# STEP 2 — Job info (no preview clutter)
# ============================================================================
tab_url, tab_text = st.tabs(["Paste job URL", "Paste job text"])

with tab_url:
    uc1, uc2 = st.columns([3, 1])
    with uc1:
        url = st.text_input("Job URL", label_visibility="collapsed", placeholder="https://...")
    with uc2:
        fetch_clicked = st.button("Fetch", use_container_width=True)
    if fetch_clicked:
        with st.spinner("Fetching..."):
            try:
                listing = fetch_job_from_url(url)
                st.session_state.job_listing = listing
                st.session_state.job_keywords = extract_keywords(listing.raw_text)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

with tab_text:
    tc1, tc2 = st.columns(2)
    with tc1:
        company_name = st.text_input("Company (optional)", key="company_input", placeholder="Company")
    with tc2:
        job_title_input = st.text_input("Job title (optional)", key="title_input", placeholder="Job title")
    job_text_input = st.text_area("Job description", height=140, label_visibility="collapsed", placeholder="Paste the full job description here...")
    if st.button("Save job description"):
        listing = build_job_listing_from_text(job_text_input, title=job_title_input, company=company_name)
        st.session_state.job_listing = listing
        st.session_state.job_keywords = extract_keywords(job_text_input)
        st.rerun()

if has_job:
    render(f'<div style="color:{GOOD}; font-size:0.85rem; margin-top:0.3rem;">✓ Job loaded · {len(st.session_state.job_keywords)} target keywords identified</div>')

st.divider()

# ============================================================================
# STEP 3 — Analysis
# ============================================================================
run_clicked = st.button("🔍 Run ATS Analysis", disabled=not has_resume, type="primary")

if not has_resume:
    st.caption("Upload a resume above to run analysis.")

if run_clicked:
    with st.spinner("Scoring resume..."):
        st.session_state.analytics_before = run_full_analysis(
            st.session_state.parsed_resume, st.session_state.resume_filename, job_keywords=st.session_state.job_keywords,
        )
    if has_job:
        with st.spinner("Running semantic gap analysis..."):
            try:
                st.session_state.gap_analysis = semantic_gap_analysis(
                    st.session_state.parsed_resume.raw_text, st.session_state.job_listing.raw_text,
                )
            except Exception as e:
                st.warning(f"Gap analysis unavailable: {e}")
        with st.spinner("Generating section feedback..."):
            try:
                st.session_state.section_feedback = section_feedback(
                    st.session_state.parsed_resume.raw_text, st.session_state.job_listing.raw_text,
                )
            except Exception as e:
                st.warning(f"Section feedback unavailable: {e}")
    st.rerun()

report = st.session_state.analytics_before
gap = st.session_state.gap_analysis

if report:
    potential_lift = min(25, len(report.missing_keywords) * 2 + (10 if report.quantified_bullet_ratio < 0.5 else 0))
    after_estimate = min(100, report.overall_score + potential_lift)
    score_color = BAD if report.overall_score < 60 else WARN if report.overall_score < 80 else GOOD

    metric_row([
        metric_box("Current ATS Score", report.overall_score, score_color),
        metric_box("Potential After Fixes", after_estimate, GOOD),
    ])
    st.caption("Full breakdown of every check lives on the Advanced Analytics page.")

# ============================================================================
# Keyword Universe — present vs missing, three rows
# ============================================================================
if gap:
    st.divider()
    render('<h4 class="gf-heading">Keyword Universe</h4>')

    rows = [
        ("Keywords", gap.get("matched_keywords", report.matched_keywords if report else []), gap.get("missing_keywords", [])),
        ("Technical Skills", gap.get("matched_technical_skills", []), gap.get("missing_technical_skills", [])),
        ("Industry Terms", gap.get("matched_industry_terms", []), gap.get("missing_industry_terms", [])),
    ]
    for label, present, missing in rows:
        render(f'<p style="color:#8B90A0; font-size:0.78rem; margin-bottom:0.15rem; text-transform:uppercase; letter-spacing:0.04em;">{label}</p>')
        pc, mc = st.columns(2)
        with pc:
            render(chips(present, "present", "None found"))
        with mc:
            render(chips(missing, "missing", "None missing 🎉"))

    render(f"""
    <div class="gf-card" style="margin-top:0.6rem;">
        <h4>Compatibility Summary</h4>
        <p>{gap.get('compatibility_summary','')}</p>
    </div>
    """)
    if gap.get("alignment_strategy"):
        render('<div class="gf-card"><h4>Alignment Strategy</h4>' + "".join(f"<p>• {s}</p>" for s in gap["alignment_strategy"]) + "</div>")

# ============================================================================
# Section-by-section: original (highlighted) vs missing terms
# ============================================================================
if report and st.session_state.parsed_resume.sections:
    st.divider()
    render('<h4 class="gf-heading">Section-by-Section: Present vs. Missing</h4>')

    all_present = list({*report.matched_keywords, *((gap or {}).get("matched_technical_skills", [])), *((gap or {}).get("matched_industry_terms", []))})
    all_missing = list({*report.missing_keywords, *((gap or {}).get("missing_technical_skills", [])), *((gap or {}).get("missing_industry_terms", []))})

    sf = st.session_state.section_feedback or {}
    for section_key in ["summary", "skills", "experience", "projects"]:
        section_text = st.session_state.parsed_resume.sections.get(section_key, "").strip()
        if not section_text:
            continue
        render(f'<p style="color:#8B90A0; font-size:0.78rem; margin:0.5rem 0 0.15rem; text-transform:uppercase; letter-spacing:0.04em;">{section_key.title()}</p>')
        lc, rc = st.columns(2)
        with lc:
            render(f'<div class="gf-card" style="max-height:260px; overflow-y:auto;"><p style="color:#E9EAF0; font-size:0.85rem; line-height:1.55;">{highlight_matches(section_text, all_present)}</p></div>')
        with rc:
            fb = sf.get(section_key, {})
            cons_html = "".join(f"<p>⚠️ {c}</p>" for c in fb.get("cons", []))
            render(f"""
            <div class="gf-card">
                <p style="color:#8B90A0; font-size:0.75rem; margin-bottom:0.4rem;">NOT CLEARLY DEMONSTRATED FOR THIS ROLE</p>
                {chips(all_missing, "missing", "Nothing missing 🎉")}
                {cons_html}
            </div>
            """)

# ============================================================================
# Weak bullet fixer (auto-detected, no manual paste needed)
# ============================================================================
if report and report.weak_bullets:
    st.divider()
    render('<h4 class="gf-heading">Bullets Missing a Metric</h4>')
    render(f'<p style="color:#8B90A0; font-size:0.85rem;">{len(report.weak_bullets)} bullet(s) in your Experience section have no number, %, or $ — these read weaker to both ATS systems and recruiters.</p>')

    if st.button("✨ Suggest fixes for these bullets"):
        with st.spinner("Rewriting..."):
            try:
                job_text = st.session_state.job_listing.raw_text if has_job else ""
                results = rewrite_bullets(report.weak_bullets, job_text)
                # Zip positionally against our own known-good originals rather than
                # trusting the model to echo them back verbatim -- this guarantees
                # the "original" text is an exact substring of the resume, which
                # the export step below depends on for reliable find/replace.
                st.session_state.weak_bullet_rewrites = [
                    {"original": orig, "rewritten": r.get("rewritten", ""), "metric_template": r.get("metric_template", "")}
                    for orig, r in zip(report.weak_bullets, results)
                ]
            except Exception as e:
                st.error(f"Couldn't rewrite bullets: {e}")

    if st.session_state.weak_bullet_rewrites:
        for item in st.session_state.weak_bullet_rewrites:
            lc, rc = st.columns(2)
            with lc:
                render(f'<div class="gf-card"><p style="color:#8B90A0; font-size:0.72rem;">CURRENT</p><p style="color:#E9EAF0;">{item.get("original","")}</p></div>')
            with rc:
                metric_line = f'<p style="color:{ACCENT_A}; font-size:0.78rem; margin-top:0.4rem;">💡 Add: {item.get("metric_template")}</p>' if item.get("metric_template") else ""
                render(f'<div class="gf-card" style="border-color:rgba(52,211,153,0.35);"><p style="color:#8B90A0; font-size:0.72rem;">SUGGESTED</p><p style="color:#E9EAF0;">{item.get("rewritten","")}</p>{metric_line}</div>')

st.divider()

# ============================================================================
# Export — side by side, no extra radio choices
# ============================================================================
if st.session_state.parsed_resume:
    render('<h4 class="gf-heading">Export</h4>')

    original_text = st.session_state.parsed_resume.raw_text
    bullet_map = {item["original"]: item["rewritten"] for item in (st.session_state.weak_bullet_rewrites or []) if item.get("rewritten")}
    modified_text = original_text
    for orig, new in bullet_map.items():
        if orig in modified_text:
            modified_text = modified_text.replace(orig, new)

    lc, rc = st.columns(2)
    with lc:
        render(f'<p style="color:#8B90A0; font-size:0.75rem;">CURRENT</p><div class="gf-card" style="max-height:320px; overflow-y:auto; white-space:pre-wrap; font-size:0.82rem;">{original_text[:4000]}</div>')
    with rc:
        render(f'<p style="color:#8B90A0; font-size:0.75rem;">MODIFIED</p><div class="gf-card" style="max-height:320px; overflow-y:auto; white-space:pre-wrap; font-size:0.82rem; border-color:rgba(52,211,153,0.3);">{modified_text[:4000]}</div>')

    is_docx_original = st.session_state.resume_filename.lower().endswith(".docx")
    if not bullet_map:
        st.caption("Run the bullet fixer above to generate a modified version to export.")
    else:
        if is_docx_original:
            st.caption("Your original DOCX's fonts, spacing, and page layout are preserved — only the fixed bullets are edited in place.")
            docx_bytes = apply_bullet_replacements_to_docx(st.session_state.resume_bytes, bullet_map)
        else:
            st.caption("Your original was a PDF, so exact layout can't be preserved — this is a clean, ATS-safe rebuild instead.")
            docx_bytes = text_to_docx("Resume", modified_text)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇️ Download DOCX", data=docx_bytes, file_name="optimized_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with dl2:
            st.download_button("⬇️ Download PDF", data=text_to_pdf("Resume", modified_text), file_name="optimized_resume.pdf",
                                mime="application/pdf", use_container_width=True)
