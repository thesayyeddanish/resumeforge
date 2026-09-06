"""Deterministic, rule-based ATS analysis.

This intentionally does NOT call the LLM — these are checks that are
cheap, explainable, and fast to run on every keystroke. The AI layer
(ai_client.py) is reserved for the fuzzier semantic work: gap analysis,
rewriting, and tone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import textstat
from spellchecker import SpellChecker

from utils.parsers import ParsedResume

PRONOUNS = {"i", "me", "my", "mine", "myself"}

ESSENTIAL_SECTIONS = ["summary", "experience", "education", "skills"]

_spell = SpellChecker(distance=1)


@dataclass
class CheckResult:
    name: str
    status: str  # "pass" | "warn" | "fail"
    detail: str
    score_impact: int = 0  # points out of 100 this check contributes


@dataclass
class AnalyticsReport:
    overall_score: int
    checks: list[CheckResult] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    quantified_bullet_ratio: float = 0.0


def _check_contact_info(resume: ParsedResume) -> CheckResult:
    missing = []
    if not resume.email:
        missing.append("email")
    if not resume.phone:
        missing.append("phone number")
    if not resume.linkedin:
        missing.append("LinkedIn URL")

    if not missing:
        return CheckResult("Contact Information", "pass", "Email, phone, and LinkedIn all detected.", 8)
    if len(missing) <= 1:
        return CheckResult("Contact Information", "warn", f"Missing: {', '.join(missing)}.", 4)
    return CheckResult("Contact Information", "fail", f"Missing: {', '.join(missing)}.", 0)


def _check_spelling_grammar(text: str) -> CheckResult:
    words = re.findall(r"[A-Za-z]+", text)
    # Filter out short tokens / likely acronyms / proper nouns (all-caps)
    candidates = [w for w in words if len(w) > 3 and not w.isupper()]
    unknown = _spell.unknown([w.lower() for w in candidates])
    # Ignore very short unknown lists — likely names/brands, not typos
    error_rate = len(unknown) / max(len(candidates), 1)

    if error_rate < 0.01:
        return CheckResult("Spelling & Grammar", "pass", "No significant spelling issues detected.", 10)
    if error_rate < 0.03:
        return CheckResult(
            "Spelling & Grammar", "warn",
            f"~{len(unknown)} possibly misspelled words found — review before submitting.", 6,
        )
    return CheckResult(
        "Spelling & Grammar", "fail",
        f"~{len(unknown)} possibly misspelled words found. This is a common ATS/recruiter red flag.", 2,
    )


def _check_personal_pronouns(text: str) -> CheckResult:
    words = re.findall(r"[A-Za-z']+", text.lower())
    pronoun_hits = sum(1 for w in words if w in PRONOUNS)
    if pronoun_hits == 0:
        return CheckResult("Personal Pronoun Usage", "pass", "No first-person pronouns found — good resume convention.", 5)
    if pronoun_hits <= 2:
        return CheckResult("Personal Pronoun Usage", "warn", f"Found {pronoun_hits} instance(s) of 'I/me/my'. Resumes should use implied first person.", 3)
    return CheckResult("Personal Pronoun Usage", "fail", f"Found {pronoun_hits} instances of personal pronouns. Remove these.", 0)


def _check_keywords(resume_text: str, job_keywords: list[str]) -> tuple[CheckResult, list[str], list[str]]:
    text_lower = resume_text.lower()
    matched, missing = [], []
    for kw in job_keywords:
        if kw.lower() in text_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    if not job_keywords:
        return (
            CheckResult("Skills & Keyword Targeting", "warn", "No job description provided yet — paste one to check keyword alignment.", 5),
            matched, missing,
        )

    coverage = len(matched) / len(job_keywords)
    if coverage >= 0.75:
        status, impact = "pass", 20
    elif coverage >= 0.45:
        status, impact = "warn", 12
    else:
        status, impact = "fail", 4

    detail = f"Matched {len(matched)}/{len(job_keywords)} target keywords ({coverage:.0%})."
    if missing:
        detail += f" Critical issue: missing required keywords — {', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}."

    return CheckResult("Skills & Keyword Targeting", status, detail, impact), matched, missing


def _check_complex_sentences(text: str) -> CheckResult:
    try:
        grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        grade = 10.0

    if grade <= 12:
        return CheckResult("Sentence Complexity", "pass", f"Reading grade level ~{grade:.1f} — clear and scannable.", 8)
    if grade <= 15:
        return CheckResult("Sentence Complexity", "warn", f"Reading grade level ~{grade:.1f} — some sentences run long. Consider shortening.", 5)
    return CheckResult("Sentence Complexity", "fail", f"Reading grade level ~{grade:.1f} — sentences are too dense for a quick recruiter scan.", 2)


def _check_quantified_points(experience_text: str) -> tuple[CheckResult, float]:
    bullets = [b.strip("•-* \t") for b in experience_text.split("\n") if len(b.strip()) > 15]
    if not bullets:
        return CheckResult("Quantified Achievements", "warn", "Couldn't isolate bullet points automatically — check manually.", 4), 0.0

    number_pattern = re.compile(r"(\$|%|\d)")
    quantified = [b for b in bullets if number_pattern.search(b)]
    ratio = len(quantified) / len(bullets)

    if ratio >= 0.5:
        return CheckResult("Quantified Achievements", "pass", f"{len(quantified)}/{len(bullets)} bullets include numbers/metrics.", 12), ratio
    if ratio >= 0.25:
        return CheckResult("Quantified Achievements", "warn", f"Only {len(quantified)}/{len(bullets)} bullets are quantified. Aim for 50%+.", 7), ratio
    return CheckResult("Quantified Achievements", "fail", f"Just {len(quantified)}/{len(bullets)} bullets have metrics. Add numbers (%, $, time saved, team size).", 2), ratio


def _check_essential_sections(resume: ParsedResume) -> CheckResult:
    found = [s for s in ESSENTIAL_SECTIONS if s in resume.sections and resume.sections[s].strip()]
    missing = [s for s in ESSENTIAL_SECTIONS if s not in found]
    if not missing:
        return CheckResult("Essential Resume Sections", "pass", "Summary, Experience, Education, and Skills all detected.", 12)
    if len(missing) == 1:
        return CheckResult("Essential Resume Sections", "warn", f"Missing section: {missing[0].title()}.", 7)
    return CheckResult("Essential Resume Sections", "fail", f"Missing sections: {', '.join(m.title() for m in missing)}.", 2)


def _check_document_properties(resume: ParsedResume, filename: str) -> CheckResult:
    issues = []
    if resume.has_photo_or_table:
        issues.append("contains embedded images/tables that some ATS parsers can misread")
    word_count = len(resume.raw_text.split())
    if word_count < 250:
        issues.append("content may be too short (under ~250 words)")
    if word_count > 1100:
        issues.append("content may be too long for a 1-2 page resume")
    if not filename.lower().endswith((".pdf", ".docx")):
        issues.append("file format is not ATS-standard (use PDF or DOCX)")

    if not issues:
        return CheckResult("Document Properties", "pass", "File format and structure look ATS-safe.", 8)
    return CheckResult("Document Properties", "warn" if len(issues) == 1 else "fail", "; ".join(issues).capitalize() + ".", 4 if len(issues) == 1 else 1)


def run_full_analysis(resume: ParsedResume, filename: str, job_keywords: list[str] | None = None) -> AnalyticsReport:
    job_keywords = job_keywords or []

    checks: list[CheckResult] = []
    checks.append(_check_contact_info(resume))
    checks.append(_check_spelling_grammar(resume.raw_text))
    checks.append(_check_personal_pronouns(resume.raw_text))

    kw_check, matched, missing = _check_keywords(resume.raw_text, job_keywords)
    checks.append(kw_check)

    checks.append(_check_complex_sentences(resume.raw_text))

    exp_text = resume.sections.get("experience", resume.raw_text)
    quant_check, ratio = _check_quantified_points(exp_text)
    checks.append(quant_check)

    checks.append(_check_essential_sections(resume))
    checks.append(_check_document_properties(resume, filename))

    overall = sum(c.score_impact for c in checks)
    overall = max(0, min(100, overall))

    return AnalyticsReport(
        overall_score=overall,
        checks=checks,
        matched_keywords=matched,
        missing_keywords=missing,
        quantified_bullet_ratio=ratio,
    )
