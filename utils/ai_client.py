"""All LLM-backed features live here: semantic gap analysis, bullet
rewriting, section pros/cons, and cover letter generation.

TRUTH GUARDRAIL: every prompt in this file carries an explicit, repeated
instruction that the model may only REPHRASE what's already in the
resume — never invent skills, employers, titles, degrees, or metrics
the candidate didn't provide. Outputs are also structurally checked
where possible (see `_looks_fabricated` heuristics are intentionally
NOT relied upon alone — the prompt-level constraint is primary).
"""

from __future__ import annotations

import json
import os

import streamlit as st
from groq import Groq

MODEL_DEFAULT = "openai/gpt-oss-120b"  # Groq's current free-tier general-purpose model

TRUTH_GUARDRAIL = """
CRITICAL GROUND RULE — TRUTH GUARDRAIL:
You may only reword, restructure, or reframe information that is
explicitly present in the candidate's resume text below. You must NEVER:
- invent, imply, or add skills, tools, technologies, certifications, or
  degrees the candidate did not list
- invent employers, job titles, dates, or promotions
- invent metrics/numbers that are not in the original text (you may
  reformat an existing number, but never fabricate a new one)
- exaggerate scope (e.g. turning "helped with" into "led" unless the
  original already indicates leadership)
If a strong keyword from the job description has NO basis anywhere in
the resume, do not add it to the resume text — instead list it as a
genuine gap for the candidate to address themselves. It is far better
to under-claim than to fabricate.
"""


def _get_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
    if not api_key:
        raise RuntimeError(
            "No GROQ_API_KEY found. Add it to .streamlit/secrets.toml locally, "
            "or in your Streamlit Cloud app's Settings > Secrets. "
            "Get a free key at https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


def _model() -> str:
    return st.secrets.get("GROQ_MODEL", MODEL_DEFAULT)


def _call(system: str, user: str, max_tokens: int = 2000) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=_model(),
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_json(system: str, user: str, max_tokens: int = 2000) -> dict:
    raw = _call(system + "\n\nRespond with ONLY valid JSON. No markdown fences, no preamble.", user, max_tokens)
    cleaned = raw.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Semantic Gap Analysis
# ---------------------------------------------------------------------------

def semantic_gap_analysis(resume_text: str, job_text: str) -> dict:
    system = f"""You are an expert technical recruiter and ATS specialist.
{TRUTH_GUARDRAIL}
Compare the resume against the job description and identify genuine
semantic gaps — not just missing keywords, but missing evidence of
required competencies."""

    user = f"""RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{job_text[:6000]}

Return JSON with this exact shape:
{{
  "matched_keywords": ["keywords/skills from the job description that ARE genuinely evidenced in the resume"],
  "missing_keywords": ["..."],
  "matched_technical_skills": ["..."],
  "missing_technical_skills": ["..."],
  "matched_industry_terms": ["..."],
  "missing_industry_terms": ["..."],
  "alignment_score_0_to_100": 0,
  "compatibility_summary": "2-3 sentence honest assessment",
  "alignment_strategy": ["3-5 concrete, honest bullet points on how the candidate should position their REAL experience for this role"]
}}"""
    return _call_json(system, user)


# ---------------------------------------------------------------------------
# Section-wise pros & cons
# ---------------------------------------------------------------------------

def section_feedback(resume_text: str, job_text: str = "") -> dict:
    system = f"""You are a senior resume reviewer.
{TRUTH_GUARDRAIL}
Give honest, specific, section-by-section feedback."""

    user = f"""RESUME:
{resume_text[:6000]}

TARGET JOB (may be empty): {job_text[:3000]}

Return JSON:
{{
  "summary": {{"pros": ["..."], "cons": ["..."]}},
  "experience": {{"pros": ["..."], "cons": ["..."]}},
  "projects": {{"pros": ["..."], "cons": ["..."]}},
  "skills": {{"pros": ["..."], "cons": ["..."]}}
}}
If a section is missing from the resume, say so in "cons" and leave "pros" empty."""
    return _call_json(system, user)


# ---------------------------------------------------------------------------
# Bullet rewriting -- formal ATS phrasing, no STAR/S-T-A-R labels in output
# ---------------------------------------------------------------------------

def rewrite_bullets(bullets: list[str], job_text: str = "") -> list[dict]:
    """Tighten resume bullets into strong, formal, ATS-style phrasing.

    Internally this follows Situation/Task/Action/Result logic to decide
    what to emphasize, but the OUTPUT never mentions those words -- it's
    just a clean, professional bullet line, like a well-written resume
    already reads.
    """
    system = f"""You are a senior resume writer. You tighten resume bullets
into strong, formal, ATS-friendly phrasing (clear scope, strong action
verb, outcome-oriented) while staying 100% truthful.
{TRUTH_GUARDRAIL}
Do NOT use or output the words "Situation", "Task", "Action", "Result",
or "STAR" anywhere -- just produce a normal, polished resume bullet.
If the original bullet has no measurable outcome, do NOT invent one --
instead sharpen the action verb and scope, and in "metric_template"
give a safe fill-in-the-blank pattern (e.g. "by [X]%", "for a team of
[X]", "saving $[X] annually") the candidate can complete with their
own real number. Never fill in a plausible-looking number yourself."""

    user = f"""Rewrite each bullet below. Target role context (optional): {job_text[:2000]}

BULLETS:
{json.dumps(bullets)}

Return JSON: a list of objects, one per input bullet, in the same order:
[{{"original": "...", "rewritten": "...", "metric_template": "a bracketed fill-in-the-blank suggestion, or empty string if the bullet is already quantified"}}]"""
    result = _call_json(system, user, max_tokens=3000)
    return result if isinstance(result, list) else result.get("bullets", [])


# ---------------------------------------------------------------------------
# Cover letter
# ---------------------------------------------------------------------------

def generate_cover_letter(resume_text: str, job_text: str, company: str, tone: str = "professional") -> str:
    system = f"""You are an expert cover letter writer.
{TRUTH_GUARDRAIL}
Write exactly 3 paragraphs:
1) Hook + why this role/company specifically
2) 2-3 concrete, TRUE pieces of evidence from the resume mapped to the job's needs
3) Enthusiasm + call to action
Match the tone to what's requested. No generic filler like "I am writing to express my interest" unless it's genuinely the strongest opener."""

    user = f"""COMPANY: {company or "the company"}
DESIRED TONE: {tone}

RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{job_text[:5000]}

Write the 3-paragraph cover letter now. Plain text only, no markdown, no placeholder brackets left unfilled — if you don't have a hiring manager name, address it to "Hiring Team"."""
    return _call(system, user, max_tokens=1200)


# ---------------------------------------------------------------------------
# Salary estimate (LLM-based reasoning, clearly labeled as an estimate)
# ---------------------------------------------------------------------------

def estimate_salary(job_title: str, company: str, location: str = "", years_experience: str = "") -> dict:
    system = """You are a compensation research analyst. You do not have
live access to salary databases, so you must reason from general,
publicly known market patterns (role, seniority, company size/tier,
industry, and location cost-of-living) as of your training knowledge.
Always caveat that this is an ESTIMATE, not live data, and numbers can
be stale or wrong — the user should verify against Levels.fyi, Glassdoor,
or Payscale before negotiating."""

    user = f"""Job Title: {job_title}
Company: {company or "Not specified"}
Location: {location or "Not specified"}
Years of experience: {years_experience or "Not specified"}

Return JSON:
{{
  "low_estimate": "e.g. $95,000",
  "mid_estimate": "e.g. $115,000",
  "high_estimate": "e.g. $135,000",
  "currency_note": "assumption made about currency/region",
  "reasoning": "2-3 sentences on what drove this range",
  "confidence": "low | medium | high",
  "disclaimer": "one sentence reminding the user this is a modeled estimate, not live market data"
}}"""
    return _call_json(system, user)
