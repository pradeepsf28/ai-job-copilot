import os

import streamlit as st
from dotenv import load_dotenv

from adzuna import AdzunaError, fetch_jobs
from analyzer import analyze_match
from hybrid_analyzer import analyze_match as analyze_match_hybrid
from job_content import generate_job_insights

load_dotenv()

ENV_ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ENV_ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()

st.set_page_config(page_title="AI Job Copilot", page_icon="🚀")
st.title("AI Job Copilot")
st.write("Welcome Pradeep 🚀")

tab_match, tab_jobs = st.tabs(["Resume Match", "Find Jobs"])

# --- Resume Match (OpenAI MVP) ---
with tab_match:
    st.caption(
        "AI-powered match analysis via OpenAI. Each run uses one API call (~gpt-4o-mini)."
    )

    with st.form("match_form"):
        resume = st.text_area("Paste Your Resume", height=200)
        job_description = st.text_area("Paste Job Description", height=200)
        submitted = st.form_submit_button("Analyze Match")

    if submitted:
        if not resume.strip() or not job_description.strip():
            st.warning("Please paste both resume and job description.")
        else:
            with st.spinner("Analyzing match..."):
                try:
                    result = analyze_match(resume, job_description)
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                else:
                    st.metric("Match score", f"{result['match_score']}%")
                    st.markdown(result["summary"])

                    st.subheader("Strong fits")
                    if result["strong_fits"]:
                        for item in result["strong_fits"]:
                            st.markdown(f"- {item}")
                    else:
                        st.info("No strong fits listed.")

                    st.subheader("Gaps")
                    if result["gaps"]:
                        for item in result["gaps"]:
                            st.markdown(f"- {item}")
                    else:
                        st.success("No major gaps identified.")

                    st.subheader("Resume improvements")
                    if result["improvements"]:
                        for item in result["improvements"]:
                            st.markdown(f"- {item}")
                    else:
                        st.info("No improvement suggestions returned.")


def _jobs_with_match_scores(
    resume: str, jobs: list[dict], employment_preference: str
) -> list[dict]:
    scored = []
    for job in jobs:
        job_text = job.get("description_full") or job.get("description", "")
        match = analyze_match_hybrid(
            resume,
            job_text,
            job_title=job.get("title", ""),
            contract_type=job.get("contract_type", ""),
            contract_time=job.get("contract_time", ""),
            employment_preference=employment_preference,
        )
        insights = generate_job_insights(resume, job, match)
        scored.append({**job, "match": match, "insights": insights})
    return sorted(scored, key=lambda j: j["match"]["match_percent"], reverse=True)


# --- Find Jobs (Adzuna + hybrid scoring) ---
with tab_jobs:
    st.caption(
        "Search Adzuna jobs ranked by hybrid local match score. "
        "Requires Adzuna credentials in `.env` or the form below."
    )

    if ENV_ADZUNA_APP_ID and ENV_ADZUNA_APP_KEY:
        st.caption("Adzuna credentials loaded from `.env` (app key is never shown).")
    elif ENV_ADZUNA_APP_ID or ENV_ADZUNA_APP_KEY:
        st.caption("Partial Adzuna credentials in `.env` — set both or enter manually.")

    with st.form("jobs_form"):
        jobs_resume = st.text_area("Paste Your Resume", height=160)
        col1, col2 = st.columns(2)
        with col1:
            app_id = st.text_input("Adzuna app_id", value=ENV_ADZUNA_APP_ID)
        with col2:
            app_key = st.text_input(
                "Adzuna app_key",
                type="password",
                placeholder=(
                    "Using app key from .env (leave blank)"
                    if ENV_ADZUNA_APP_KEY
                    else "Enter app key"
                ),
            )
        job_title = st.text_input("Job title", placeholder="e.g. Product Manager")
        location = st.text_input("Location", placeholder="e.g. New York")
        employment_type = st.radio(
            "Employment type",
            options=["Contract", "Full Time", "Both"],
            horizontal=True,
        )
        find_jobs = st.form_submit_button("Find Jobs")

    if find_jobs:
        resolved_app_id = app_id.strip() or ENV_ADZUNA_APP_ID
        resolved_app_key = app_key.strip() or ENV_ADZUNA_APP_KEY

        if not jobs_resume.strip():
            st.warning("Paste your resume to analyze job matches.")
        elif not resolved_app_id or not resolved_app_key:
            st.warning(
                "Adzuna credentials missing. Add ADZUNA_APP_ID and ADZUNA_APP_KEY "
                "to `.env`, or enter them in the form."
            )
        elif not job_title.strip() or not location.strip():
            st.warning("Enter both a job title and location.")
        else:
            with st.spinner("Fetching jobs and analyzing matches..."):
                try:
                    jobs = fetch_jobs(
                        app_id=resolved_app_id,
                        app_key=resolved_app_key,
                        job_title=job_title,
                        location=location,
                        employment_type=employment_type,
                    )
                    jobs = _jobs_with_match_scores(
                        jobs_resume, jobs, employment_type
                    )
                except AdzunaError as e:
                    st.error(str(e))
                else:
                    if not jobs:
                        st.info("No jobs found. Try a broader title or location.")
                    else:
                        st.success(
                            f"Found {len(jobs)} jobs, ranked by match score (highest first)."
                        )
                        for index, job in enumerate(jobs):
                            match = job["match"]
                            insights = job["insights"]
                            pct = match["match_percent"]
                            label = match["match_label"]
                            header = f"#{index + 1} · {job['title']} — {pct}% · {label}"

                            with st.expander(header, expanded=index == 0):
                                c1, c2 = st.columns([1, 3])
                                with c1:
                                    st.metric("Match %", f"{pct}%", label)
                                with c2:
                                    st.markdown(f"**{job['company']}** · {job['location']}")
                                    st.markdown(f"Salary: {job['salary']}")

                                if match.get("is_internship"):
                                    st.warning(
                                        "Internship role — not recommended as a strong "
                                        "match for experienced PM candidates."
                                    )

                                st.markdown(f"##### {insights['fit_heading']}")
                                for point in insights["fit_points"]:
                                    st.markdown(f"- {point}")

                                with st.expander("Score breakdown", expanded=False):
                                    b = match["score_breakdown"]
                                    st.markdown(
                                        f"- Skills: **{b['skills']}** · Role: **{b['role']}** · "
                                        f"Seniority: **{b['seniority']}** · Domain: **{b['domain']}** · "
                                        f"Employment: **{b['employment']}**"
                                    )

                                m, miss = match["matching_skills"], match["missing_skills"]
                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    st.markdown(
                                        "**Matching skills**  \n"
                                        + (", ".join(m[:8]) if m else "None")
                                    )
                                with sc2:
                                    if miss:
                                        st.markdown("**Missing skills**  \n" + ", ".join(miss[:8]))

                                with st.expander("Tailored Summary", expanded=False):
                                    st.markdown(insights["tailored_summary"])
                                with st.expander("Recruiter Email Draft", expanded=False):
                                    st.markdown(insights["recruiter_email"])

                                st.divider()
                                st.markdown(f"**Job snippet**  \n{job['description']}")
                                if job["url"]:
                                    st.link_button("View on Adzuna", job["url"])
