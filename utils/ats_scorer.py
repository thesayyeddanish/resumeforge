"""Deterministic, rule-based ATS analysis.

No LLM calls here -- fast, free, explainable. The AI layer (ai_client.py)
handles the fuzzier semantic work. Every check returns a 1-10 rating
plus a `data` dict with whatever rich detail its page needs to render
(actual misspelled words, actual pronoun sentences, actual weak
bullets -- never just a pass/fail label).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean

import textstat
from spellchecker import SpellChecker

from utils.parsers import ParsedResume

PRONOUNS = {"i", "me", "my", "mine", "myself"}
ESSENTIAL_SECTIONS = ["summary", "experience", "education", "skills"]

_spell = SpellChecker(distance=1)


@dataclass
class CheckResult:
    name: str
    rating: int  # 1-10
    summary: str
    data: dict = field(default_factory=dict)


@dataclass
class AnalyticsReport:
    overall_score: int  # 0-100, for comparability with "ATS score" language elsewhere
    checks: list[CheckResult] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    quantified_bullet_ratio: float = 0.0
    weak_bullets: list[str] = field(default_factory=list)


def _check_contact_info(resume: ParsedResume) -> CheckResult:
    fields = {"Email": bool(resume.email), "Phone": bool(resume.phone), "LinkedIn": bool(resume.linkedin)}
    count = sum(fields.values())
    rating = {3: 10, 2: 6, 1: 3, 0: 1}[count]
    missing = [k for k, v in fields.items() if not v]
    summary = "All key contact fields found." if not missing else f"Missing: {', '.join(missing)}."
    return CheckResult("Contact Information", rating, summary, {"fields": fields})


def _check_spelling_grammar(text: str) -> CheckResult:
    words = re.findall(r"[A-Za-z]+", text)
    candidates = [w for w in words if len(w) > 3 and not w.isupper()]
    unknown = sorted(_spell.unknown([w.lower() for w in candidates]))
    error_rate = len(unknown) / max(len(candidates), 1)

    if error_rate < 0.01:
        rating = 10
    elif error_rate < 0.02:
        rating = 8
    elif error_rate < 0.035:
        rating = 6
    elif error_rate < 0.05:
        rating = 4
    else:
        rating = 2

    summary = "No significant spelling issues detected." if not unknown else f"{len(unknown)} possibly misspelled word(s) found."
    return CheckResult("Spelling & Grammar", rating, summary, {"misspelled": unknown[:25]})


def _check_personal_pronouns(text: str) -> CheckResult:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    examples = []
    hits = 0
    for line in lines:
        words = re.findall(r"[A-Za-z']+", line.lower())
        found = [w for w in words if w in PRONOUNS]
        if found:
            hits += len(found)
            if len(examples) < 6:
                examples.append(line)

    rating = 10 if hits == 0 else 6 if hits <= 2 else 3
    summary = "No first-person pronouns found." if hits == 0 else f"Found {hits} instance(s) of personal pronouns."
    return CheckResult("Personal Pronoun Usage", rating, summary, {"examples": examples, "count": hits})


def _check_keywords(resume_text: str, job_keywords: list[str]) -> tuple[CheckResult, list[str], list[str]]:
    text_lower = resume_text.lower()
    matched, missing = [], []
    for kw in job_keywords:
        (matched if kw.lower() in text_lower else missing).append(kw)

    if not job_keywords:
        return (
            CheckResult("Skills & Keyword Targeting", 5, "No job description loaded yet -- add one to check keyword alignment.", {"matched": [], "missing": []}),
            matched, missing,
        )

    coverage = len(matched) / len(job_keywords)
    rating = 9 if coverage >= 0.75 else 7 if coverage >= 0.5 else 4 if coverage >= 0.25 else 2
    summary = f"Matched {len(matched)}/{len(job_keywords)} target keywords ({coverage:.0%})."
    return CheckResult("Skills & Keyword Targeting", rating, summary, {"matched": matched, "missing": missing, "coverage": coverage}), matched, missing


def _check_complex_sentences(text: str) -> CheckResult:
    try:
        grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        grade = 10.0

    rating = 9 if grade <= 10 else 7 if grade <= 12 else 5 if grade <= 15 else 3
    summary = f"Reading grade level ~{grade:.1f}."
    return CheckResult("Sentence Complexity", rating, summary, {"grade": grade})


def _check_quantified_points(experience_text: str) -> tuple[CheckResult, float, list[str]]:
    bullets = [b.strip("•-* \t") for b in experience_text.split("\n") if len(b.strip()) > 15]
    if not bullets:
        return CheckResult("Quantified Achievements", 5, "Couldn't isolate bullet points automatically.", {"weak_bullets": [], "target_ratio": 0.5}), 0.0, []

    number_pattern = re.compile(r"(\$|%|\d)")
    weak = [b for b in bullets if not number_pattern.search(b)]
    ratio = (len(bullets) - len(weak)) / len(bullets)

    rating = 9 if ratio >= 0.6 else 7 if ratio >= 0.4 else 4 if ratio >= 0.2 else 2
    summary = f"{len(bullets) - len(weak)}/{len(bullets)} bullets include a number, %, or $ metric."
    return CheckResult("Quantified Achievements", rating, summary, {"weak_bullets": weak[:10], "target_ratio": 0.5}), ratio, weak[:10]


def _check_essential_sections(resume: ParsedResume) -> CheckResult:
    found = [s for s in ESSENTIAL_SECTIONS if s in resume.sections and resume.sections[s].strip()]
    missing = [s for s in ESSENTIAL_SECTIONS if s not in found]
    rating = 10 if not missing else 6 if len(missing) == 1 else 3
    summary = "All essential sections detected." if not missing else f"Missing: {', '.join(m.title() for m in missing)}."
    return CheckResult("Essential Resume Sections", rating, summary, {"found": found, "missing": missing})


def _check_document_properties(resume: ParsedResume, filename: str) -> CheckResult:
    issues = []
    if resume.has_photo_or_table:
        issues.append("Contains embedded images or tables, which some ATS parsers misread as blank space or garbled text.")
    word_count = len(resume.raw_text.split())
    if word_count < 250:
        issues.append(f"Content is quite short ({word_count} words) -- ATS parsers and recruiters may read this as underdeveloped.")
    if word_count > 1100:
        issues.append(f"Content is long ({word_count} words) -- consider trimming to keep it to roughly 1-2 pages.")
    if not filename.lower().endswith((".pdf", ".docx")):
        issues.append("File format isn't a standard ATS-safe type (use PDF or DOCX).")

    rating = 10 if not issues else 6 if len(issues) == 1 else 3
    summary = "File format and structure look ATS-safe." if not issues else f"{len(issues)} issue(s) found."
    return CheckResult("Document Properties", rating, summary, {"issues": issues})


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
    quant_check, ratio, weak_bullets = _check_quantified_points(exp_text)
    checks.append(quant_check)

    checks.append(_check_essential_sections(resume))
    checks.append(_check_document_properties(resume, filename))

    overall = round(mean(c.rating for c in checks) * 10)

    return AnalyticsReport(
        overall_score=max(0, min(100, overall)),
        checks=checks,
        matched_keywords=matched,
        missing_keywords=missing,
        quantified_bullet_ratio=ratio,
        weak_bullets=weak_bullets,
    )
