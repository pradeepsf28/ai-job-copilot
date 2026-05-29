"""Fetch job listings from the Adzuna API."""

import re

import requests

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
DEFAULT_COUNTRY = "us"
RESULTS_PER_PAGE = 20


class AdzunaError(Exception):
    pass


def fetch_jobs(
    app_id: str,
    app_key: str,
    job_title: str,
    location: str,
    employment_type: str,
    country: str = DEFAULT_COUNTRY,
) -> list[dict]:
    """
    Search Adzuna for jobs.

    employment_type: "Contract", "Full Time", or "Both"
    """
    params = {
        "app_id": app_id.strip(),
        "app_key": app_key.strip(),
        "what": job_title.strip(),
        "where": location.strip(),
        "results_per_page": RESULTS_PER_PAGE,
        "content-type": "application/json",
    }

    if employment_type == "Contract":
        params["contract"] = 1
    elif employment_type == "Full Time":
        params["full_time"] = 1
    # "Both" = no extra filter; we sort contract roles first below

    url = ADZUNA_BASE.format(country=country)
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as e:
        detail = str(e)
        if e.response is not None:
            try:
                detail = e.response.json().get("exception", "") or e.response.text[:200]
            except Exception:
                detail = e.response.text[:200] or detail
            raise AdzunaError(
                f"Adzuna API error ({e.response.status_code}): {detail}"
            ) from e
        raise AdzunaError(f"Adzuna API error: {detail}") from e
    except requests.RequestException as e:
        raise AdzunaError(f"Could not reach Adzuna API: {e}") from e

    data = response.json()
    raw_jobs = data.get("results", [])
    sorted_jobs = _sort_contract_first(raw_jobs)
    return [_format_job(job) for job in sorted_jobs]


def _sort_contract_first(jobs: list[dict]) -> list[dict]:
    """Put contract roles before other roles."""

    def rank(job: dict) -> int:
        contract_type = (job.get("contract_type") or "").lower()
        if contract_type == "contract":
            return 0
        if job.get("contract_time") == "full_time":
            return 1
        return 2

    return sorted(jobs, key=rank)


def _format_job(job: dict) -> dict:
    company = job.get("company") or {}
    location = job.get("location") or {}

    return {
        "title": job.get("title") or "Untitled role",
        "company": company.get("display_name") or "Company not listed",
        "location": location.get("display_name") or "Location not listed",
        "salary": _format_salary(job.get("salary_min"), job.get("salary_max")),
        "description": _clean_snippet(job.get("description", "")),
        "description_full": _clean_description(job.get("description", "")),
        "contract_type": job.get("contract_type") or "",
        "contract_time": job.get("contract_time") or "",
        "url": job.get("redirect_url") or "",
    }


def _format_salary(salary_min, salary_max) -> str:
    if salary_min and salary_max:
        return f"${salary_min:,.0f} – ${salary_max:,.0f}"
    if salary_min:
        return f"From ${salary_min:,.0f}"
    if salary_max:
        return f"Up to ${salary_max:,.0f}"
    return "Not listed"


def _clean_description(text: str, max_length: int = 8000) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_length:
        return text
    return text[:max_length]


def _clean_snippet(text: str, max_length: int = 280) -> str:
    cleaned = _clean_description(text, max_length=max_length)
    if not cleaned:
        return "No description available."
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."
