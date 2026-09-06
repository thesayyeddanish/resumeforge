import streamlit as st

from utils.styling import inject_css, hero
from utils.ai_client import generate_cover_letter
from utils.exporter import text_to_docx, text_to_pdf

st.set_page_config(page_title="Cover Letter • ResumeForge AI", page_icon="✉️", layout="wide")
inject_css()
hero("✉️ Tailored Cover Letter Generator", "A clean, 3-paragraph cover letter matched to the company's tone — grounded only in your real experience.")

if not st.session_state.get("parsed_resume"):
    st.warning("Upload a resume on the **Resume Optimizer** page first.")
    st.stop()

job_listing = st.session_state.get("job_listing")
job_text_default = job_listing.raw_text if job_listing else ""
company_default = job_listing.company if job_listing else ""

st.markdown("### Details")
c1, c2 = st.columns(2)
with c1:
    company = st.text_input("Target company", value=company_default)
with c2:
    tone = st.selectbox("Tone", ["Professional", "Warm & personable", "Confident & direct", "Startup-casual", "Formal/corporate"])

job_text = st.text_area("Job description (auto-filled if set on Resume Optimizer page)", value=job_text_default, height=200)

if st.button("✍️ Generate Cover Letter", use_container_width=False):
    if not job_text.strip():
        st.warning("Paste a job description first — the letter needs something to tailor to.")
    else:
        with st.spinner("Drafting your cover letter..."):
            try:
                letter = generate_cover_letter(
                    st.session_state.parsed_resume.raw_text,
                    job_text,
                    company,
                    tone.lower(),
                )
                st.session_state.cover_letter_text = letter
            except Exception as e:
                st.error(f"Couldn't generate cover letter: {e}")

if st.session_state.get("cover_letter_text"):
    st.markdown("### Your Cover Letter")
    edited = st.text_area("Edit if needed", value=st.session_state.cover_letter_text, height=350, key="cl_edit")
    st.session_state.cover_letter_text = edited

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "⬇️ Download as DOCX",
            data=text_to_docx("Cover Letter", edited),
            file_name="cover_letter.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇️ Download as PDF",
            data=text_to_pdf("Cover Letter", edited),
            file_name="cover_letter.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
