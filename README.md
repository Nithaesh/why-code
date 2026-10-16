# WhyCode

WhyCode investigates Git history to answer why code changed, with evidence-backed commit citations. This repository currently contains **Phase 0 only**: project setup, an LLM provider interface, Gemini integration, disk caching, and tests.

## Requirements
- Python 3.11
- Git (for later phases)
- A Gemini API key for the live API demonstration

## Setup (Windows PowerShell)
```powershell
cd D:\Nithaesh\Programming\whycode
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env
```
Edit `.env` and set `GEMINI_API_KEY` to your own key. Never commit `.env`.

## Run the small caching experiment
```powershell
python experiments\cache_demo.py
```

## Run tests (no API key or paid API request needed)
```powershell
python -m pytest -q
```

## Run the Gemini smoke test
```powershell
python -m whycode.hello
```
Run it twice with the same configuration and prompt. The first run should report `Cache hit: False`; the second should report `Cache hit: True`, provided the first call succeeded and the cache files were not removed.

## Notes
- The default model is configured by `GEMINI_MODEL` in `.env`; the example uses `gemini-3.8-flash`. Confirm model availability and current free-tier limits in the official Gemini documentation for your account.
- The cache is a local application response cache, not Gemini's server-side context caching feature.
- Phase 0 does not yet read Git repositories, create embeddings, or implement RAG/agents.
