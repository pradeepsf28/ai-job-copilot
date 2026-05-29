# AI Job Copilot

Streamlit app to compare your resume against job descriptions and search live jobs.

## Setup

1. Install dependencies:

   ```bash
   py -m pip install -r requirements.txt
   ```

2. Copy environment file and add keys:

   ```bash
   copy .env.example .env
   ```

   - `OPENAI_API_KEY` — required for **Resume Match** (https://platform.openai.com/api-keys)
   - `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` — optional, for **Find Jobs** (https://developer.adzuna.com/signup)

3. Run the app:

   ```bash
   py -m streamlit run app.py
   ```

## Features

- **Resume Match** — OpenAI analysis (`gpt-4o-mini`): match score, strong fits, gaps, resume improvements
- **Find Jobs** — Adzuna search with hybrid local scoring and outreach copy

## Cost note

Each **Analyze Match** uses one OpenAI request (~2–8k tokens). `gpt-4o-mini` is inexpensive for personal use.

## Security

Never commit `.env` (listed in `.gitignore`).
