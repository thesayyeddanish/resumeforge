"""Pull job description text from a URL or raw paste, and derive
target keywords used by the ATS keyword-matching check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# A generic stoplist plus resume-irrelevant boilerplate often found in JDs
STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "are", "will", "have",
    "this", "that", "from", "who", "job", "role", "team", "work", "years",
    "experience", "ability", "strong", "skills", "including", "etc", "such",
    "into", "across", "within", "using", "must", "able", "candidate", "candidates",
    "we", "us", "an", "as", "is", "be", "of", "to", "in", "on", "or", "a",
}


@dataclass
class JobListing:
    title: str = ""
    company: str = ""
    raw_text: str = ""


def fetch_job_from_url(url: str) -> JobListing:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(
            f"Couldn't fetch that URL ({e}). Many job boards block scrapers — "
            "try pasting the job description text instead."
        )

    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{2,}", "\n\n", text).strip()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    return JobListing(title=title, raw_text=text)


def build_job_listing_from_text(text: str, title: str = "", company: str = "") -> JobListing:
    return JobListing(title=title, company=company, raw_text=text.strip())


def extract_keywords(job_text: str, top_n: int = 30) -> list[str]:
    """Lightweight noun-phrase-ish keyword extraction without heavy NLP deps.

    Grabs capitalized multi-word terms (likely tools/tech/proper nouns) plus
    frequent single words after stopword removal, then dedupes.
    """
    if not job_text:
        return []

    # Multi-word tech-ish terms: "Machine Learning", "Google Cloud Platform"
    multiword = re.findall(r"\b([A-Z][a-zA-Z0-9+#.]*(?:\s[A-Z][a-zA-Z0-9+#.]*){0,2})\b", job_text)
    multiword = [m.strip() for m in multiword if 1 < len(m.split()) <= 3 or m.isupper()]

    # Also grab common single-token tech keywords (e.g. Python, SQL, AWS)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}", job_text)
    freq: dict[str, int] = {}
    for t in tokens:
        low = t.lower()
        if low in STOPWORDS or len(low) < 3:
            continue
        freq[t] = freq.get(t, 0) + 1

    single_ranked = sorted(freq.items(), key=lambda kv: -kv[1])
    singles = [w for w, c in single_ranked if c >= 2][: top_n]

    combined = []
    seen_lower = set()
    for term in multiword + singles:
        key = term.lower()
        if key not in seen_lower:
            seen_lower.add(key)
            combined.append(term)

    return combined[:top_n]
