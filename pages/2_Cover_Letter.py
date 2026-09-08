import hashlib

import streamlit as st

from utils.styling import inject_css, topbar, render
from utils.state import init_state
from utils.ai_client import generate_cover_letter
from utils.exporter import text_to_docx, text_to_pdf

st.set_page_config(page_title="Cover Letter • ResumeForge AI", page_icon="✉️", layout="wide")
inject_css()
init_state()

topbar("✉️ Cover Letter", "A 3-paragraph letter matched to the company's tone — grounded only in your real experience.")

if not st.session_state.get("parsed_resume"):
    st.warning("Upload a resume on the Resume Optimizer page first.")
    st.stop()

job_listing = st.session_state.get("job_listing")
job_text_default = job_listing.raw_text if job_listing else ""
company_default = job_listing.company if job_listing else ""

c1, c2 = st.columns(2)
with c1:
    company = st.text_input("Target company", value=company_default, placeholder="Company")
with c2:
    tone = st.selectbox("Tone", ["Professional", "Warm & personable", "Confident & direct", "Startup-casual", "Formal/corporate"], label_visibility="visible")

with st.expander("Job description", expanded=not job_text_default):
    job_text = st.text_area("Job description", value=job_text_default, height=130, label_visibility="collapsed",
                             placeholder="Paste a job description if you haven't already added one on Resume Optimizer.")

# Auto-generate: if a job + resume are present and nothing has changed since
# the last generation, skip re-calling the model on every rerun.
cache_key = hashlib.sha256(f"{st.session_state.parsed_resume.raw_text}|{job_text}|{company}|{tone}".encode()).hexdigest()
should_generate = job_text.strip() and st.session_state.cover_letter_cache_key != cache_key

if should_generate:
    with st.spinner("Drafting your cover letter..."):
        try:
            st.session_state.cover_letter_text = generate_cover_letter(
                st.session_state.parsed_resume.raw_text, job_text, company, tone.lower(),
            )
            st.session_state.cover_letter_cache_key = cache_key
        except Exception as e:
            st.error(f"Couldn't generate cover letter: {e}")

if not job_text.strip():
    st.caption("Add a job description above to generate a letter.")
elif st.button("🔁 Regenerate"):
    st.session_state.cover_letter_cache_key = None
    st.rerun()

if st.session_state.get("cover_letter_text"):
    edited = st.text_area("Your letter", value=st.session_state.cover_letter_text, height=320, label_visibility="collapsed")
    st.session_state.cover_letter_text = edited

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("⬇️ DOCX", data=text_to_docx("Cover Letter", edited), file_name="cover_letter.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with dl2:
        st.download_button("⬇️ PDF", data=text_to_pdf("Cover Letter", edited), file_name="cover_letter.pdf",
                            mime="application/pdf", use_container_width=True)
    with dl3:
        with st.popover("📋 Copy as text", use_container_width=True):
            st.code(edited, language=None)
            st.caption("Click the copy icon in the top-right of the box above.")
