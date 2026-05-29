"""OpenAI-powered resume vs. job description match (MVP)."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAX_INPUT_CHARS = 12_000

SYSTEM_PROMPT = """You are an expert career coach. Compare the candidate resume to the job description.
Return only valid JSON with this exact shape:
{
  "match_score": <integer 0-100>,
  "summary": "<one sentence overall fit>",
  "strong_fits": ["<bullet>", "..."],
  "gaps": ["<missing skill or requirement>", "..."],
  "improvements": ["<concrete resume edit>", "..."]
}
Be specific to the pasted texts. Do not invent experience not implied by the resume."""


def _truncate(text: str, label: str) -> str:
    if len(text) <= MAX_INPUT_CHARS:
        return text
    return text[:MAX_INPUT_CHARS] + f"\n\n[{label} truncated to {MAX_INPUT_CHARS} characters]"


def analyze_match(resume: str, job_description: str) -> dict:
    """
    Compare resume to job description using OpenAI (gpt-4o-mini, JSON mode).

    Returns match_score, summary, strong_fits, gaps, improvements.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your OpenAI API key."
        )

    resume = _truncate(resume.strip(), "Resume")
    job_description = _truncate(job_description.strip(), "Job description")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"## Resume\n{resume}\n\n## Job Description\n{job_description}"
                ),
            },
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    required = ("match_score", "summary", "strong_fits", "gaps", "improvements")
    for key in required:
        if key not in data:
            raise ValueError(f"Model response missing field: {key}")

    data["match_score"] = max(0, min(100, int(data["match_score"])))
    return data
