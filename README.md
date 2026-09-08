# 🧠 ResumeForge AI

An all-in-one job application co-pilot built with Streamlit: resume ATS
optimizer, semantic gap analysis, STAR bullet rewriter, tailored cover
letter generator, and a salary range estimator — all in one clean,
modern web app.

## Features

- **Import Resume** — PDF or DOCX upload
- **Auto-Extract Job Info** — paste a job URL or raw text
- **ATS Score Comparison** — current vs. potential score
- **Semantic Gap Analysis** — missing keywords, skills, industry terms
- **Section-wise Pros & Cons** — Summary / Experience / Projects / Skills
- **Salary Range Estimator** — modeled estimate by title/company/location
- **STAR-Method Bullet Optimizer** — with side-by-side original vs. AI view
- **Truth Guardrail** — the AI only rephrases real experience, never invents it
- **Tailored Cover Letter Generator** — 3-paragraph, tone-matched
- **ATS-Friendly Export** — download as PDF or DOCX
- **Advanced Analytics** — the full recruiter-style diagnostic checklist

## Project structure

```
resumeforge/
├── Home.py                         # Landing page + global session state
├── pages/
│   ├── 1_📄_Resume_Optimizer.py
│   ├── 2_✉️_Cover_Letter.py
│   ├── 3_💰_Salary_Estimator.py
│   └── 4_📊_Advanced_Analytics.py
├── utils/
│   ├── parsers.py        # PDF/DOCX text extraction
│   ├── ats_scorer.py     # Rule-based ATS scoring (no AI needed)
│   ├── job_intel.py      # Job URL scraping + keyword extraction
│   ├── ai_client.py      # Claude API calls (gap analysis, rewriting, cover letters)
│   ├── exporter.py       # DOCX/PDF export
│   └── styling.py        # Shared modern CSS theme
├── .streamlit/
│   ├── config.toml               # Theme colors
│   └── secrets_example.toml      # Template — copy to secrets.toml locally
├── requirements.txt
└── .gitignore
```

## 1. Local setup

```bash
git clone https://github.com/<your-username>/resumeforge.git
cd resumeforge
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the secrets template and add your **free Groq API key**
(get one at https://console.groq.com/keys — no billing required,
just create a free account):

```bash
cp .streamlit/secrets_example.toml .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your real key
```

Run locally:

```bash
streamlit run Home.py
```

## 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: ResumeForge AI"
git branch -M main
git remote add origin https://github.com/<your-username>/resumeforge.git
git push -u origin main
```

`secrets.toml` is already in `.gitignore` — **never commit your real API
key**. Only `secrets_example.toml` should go to GitHub.

## 3. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **New app**, pick your repo/branch, and set the main file to `Home.py`.
3. Before (or after) deploying, go to **Settings → Secrets** on the app
   and paste in:
   ```toml
   GROQ_API_KEY = "gsk_your-real-key"
   GROQ_MODEL = "openai/gpt-oss-120b"
   ```
4. Deploy. Streamlit Cloud will install `requirements.txt` automatically.

## ⚠️ If you're updating an existing deployment

The entry file was renamed from `app.py` to `Home.py` (so the sidebar
nav shows "Home" instead of "app"). If your app is already deployed:

1. Upload/push all the new files as usual.
2. **Delete the old `app.py`** from your repo — otherwise both files
   will exist and confuse the deploy.
3. On Streamlit Community Cloud, go to your app's **Settings → General**
   and change **Main file path** from `app.py` to `Home.py`.
4. Reboot the app.

## Notes & honest limitations (read this before you ship it)

- **This app runs on Groq's free tier** (`openai/gpt-oss-120b`) by
  default — no billing account needed. Free tier limits are roughly
  30 requests/minute with a daily token cap, which is plenty for
  personal use and demos. **Heads up: Groq periodically retires model
  names** (it happened to `llama-3.3-70b-versatile`, which this app
  used until August 2026). If a feature suddenly errors with
  `model_not_found`, check https://console.groq.com/docs/models for
  the current lineup and update `GROQ_MODEL` in your secrets — no code
  change needed, since the app reads the model name from there.
  (We originally built this on Google's Gemini free tier, but switched
  after Google's newly-issued "AQ."-prefix API keys hit an ongoing,
  unresolved authentication bug on their generateContent endpoint —
  see https://discuss.ai.google.dev if curious.)
- **Salary Estimator** uses the LLM's general knowledge to *model* a
  range — it is not pulling live data from Glassdoor/Levels.fyi (no
  free public API exists for that). The app clearly labels this as an
  estimate. If you want live data later, look at paid APIs like
  Levels.fyi's or a scraping approach (fragile, ToS-sensitive).
- **Job URL scraping** works on many company career pages but will be
  blocked by sites with heavy bot protection (LinkedIn, Indeed in many
  cases). The "paste text" tab is the reliable fallback — keep it front
  and center in your UI rather than treating it as a backup.
- **Export format fidelity**: for a DOCX-uploaded resume, exporting
  edits your ORIGINAL file in place (only the fixed bullets change —
  fonts, margins, and page count stay exactly as they were). For a
  PDF-uploaded resume, true layout preservation isn't possible (PDF
  text extraction loses formatting information), so export instead
  produces a clean, single-column ATS-safe rebuild. The app tells you
  which mode applies before you download.
- **Section splitting** (Summary/Experience/etc.) uses simple heading
  detection. Resumes with unconventional formatting (heavy tables,
  multi-column layouts, creative headers) may not split perfectly —
  this is also *why* those layouts hurt real ATS parsing, so flagging
  it doubles as a feature.
- **Spelling check** uses a lightweight pure-Python spellchecker
  (`pyspellchecker`) instead of LanguageTool, because LanguageTool
  needs a JVM that isn't available on Streamlit Community Cloud. It's
  less thorough on grammar (vs. spelling) — if you want deeper grammar
  checking, route that specific check through the Claude API instead.
- **Cost**: every AI-powered click (gap analysis, section feedback,
  STAR rewrite, cover letter, salary estimate) is a real API call
  billed to your Anthropic account. Consider adding simple caching
  (`st.cache_data`) keyed on resume+job text if you expect heavy reuse.

## Roadmap ideas

- Swap the salary estimator to a real compensation API when you find
  one with a usable free/cheap tier.
- Add authentication (Streamlit supports OAuth via `st.experimental_user`
  or third-party libs) if you want multi-user history.
- Persist resume versions in a database (Supabase/Postgres) instead of
  only `st.session_state`, which resets on refresh.
- Add a diff-highlighted view (not just side-by-side) for bullet edits.
