"""Generate tailored summaries and recruiter emails from resume + job match data."""


def generate_job_insights(resume: str, job: dict, match: dict) -> dict:
    matching = match.get("matching_skills", [])
    missing = match.get("missing_skills", [])
    pct = match.get("match_percent", 0)
    label = match.get("match_label", "Low match")
    is_internship = match.get("is_internship", False)

    title = job.get("title", "this role")
    company = job.get("company", "the company")
    location = job.get("location", "")

    return {
        "fit_points": _fit_points(pct, label, matching, missing, title, company, is_internship),
        "fit_heading": _fit_heading(label),
        "tailored_summary": _tailored_summary(
            title, company, location, pct, label, matching, missing, is_internship
        ),
        "recruiter_email": _recruiter_email(title, company, matching, pct, label),
    }


def _fit_heading(match_label: str) -> str:
    if match_label == "Strong match":
        return "Why you're a strong fit"
    if match_label == "Good match":
        return "Why you're a good fit"
    if match_label == "Moderate match":
        return "Moderate fit highlights"
    return "Match highlights"


def _fit_points(
    pct: int,
    label: str,
    matching: list[str],
    missing: list[str],
    title: str,
    company: str,
    is_internship: bool,
) -> list[str]:
    points = []

    if is_internship:
        points.append(
            "This is an **internship** role—typically a **low match** for experienced "
            "product professionals unless you are actively seeking an intern program."
        )

    points.append(
        f"Hybrid score: **{label}** ({pct}%) for **{title}** at **{company}**."
    )

    if label == "Strong match" and matching:
        top = ", ".join(matching[:4])
        points.append(
            f"Strong alignment on priority skills including **{top}**."
        )
    elif label == "Good match" and matching:
        top = ", ".join(matching[:4])
        points.append(
            f"Solid overlap on **{top}**, supporting a credible application narrative."
        )
    elif label == "Moderate match":
        points.append(
            "Role title and seniority show partial alignment; strengthen skill keywords on your resume."
        )
    else:
        points.append(
            "Limited overlap detected—consider whether this role matches your target path before applying."
        )

    if len(matching) >= 3:
        points.append(
            f"**{len(matching)}** skills/groups matched—breadth beyond a single keyword."
        )

    if missing and pct >= 60:
        gap = ", ".join(missing[:3])
        points.append(f"Address gaps in **{gap}** if you have adjacent experience.")

    return points[:4]


def _tailored_summary(
    title: str,
    company: str,
    location: str,
    pct: int,
    label: str,
    matching: list[str],
    missing: list[str],
    is_internship: bool,
) -> str:
    loc = f" in {location}" if location and location != "Location not listed" else ""
    skills_line = ", ".join(matching[:5]) if matching else "transferable product experience"

    if is_internship:
        opener = (
            f"**{label}** ({pct}%) for **{title}** at **{company}**{loc}. "
            f"This internship is unlikely to be a strong target for a senior PM profile."
        )
    elif label == "Strong match":
        opener = (
            f"**{label}** ({pct}%) for **{title}** at **{company}**{loc}. "
            f"You present a compelling hybrid alignment across skills and role fit."
        )
    elif label == "Good match":
        opener = (
            f"**{label}** ({pct}%) for **{title}** at **{company}**{loc}. "
            f"You are well positioned with clear skill and role overlap."
        )
    elif label == "Moderate match":
        opener = (
            f"**{label}** ({pct}%) for **{title}** at **{company}**{loc}. "
            f"Worth exploring with a tailored resume emphasis."
        )
    else:
        opener = (
            f"**{label}** ({pct}%) for **{title}** at **{company}**{loc}. "
            f"Consider prioritizing roles with stronger skill alignment."
        )

    body = f"Highlight **{skills_line}** when customizing your application."

    if missing and pct >= 40:
        develop = ", ".join(missing[:3])
        closer = f"Bridge gaps around **{develop}** with specific outcomes if applicable."
    else:
        closer = "Lead with quantified impact and product outcomes in your materials."

    return f"{opener} {body} {closer}"


def _recruiter_email(
    title: str,
    company: str,
    matching: list[str],
    pct: int,
    label: str,
) -> str:
    skills_phrase = ", ".join(matching[:4]) if matching else "product delivery and stakeholder leadership"

    if label == "Strong match":
        fit_line = (
            f"My background is a **strong match** ({pct}%) for your posting, "
            f"including {skills_phrase}."
        )
    elif label == "Good match":
        fit_line = (
            f"I see a **good match** ({pct}%) with your requirements, "
            f"particularly in {skills_phrase}."
        )
    elif label == "Moderate match":
        fit_line = (
            f"I believe I can add value in the **{title}** role ({pct}% alignment) "
            f"and bring experience in {skills_phrase}."
        )
    else:
        fit_line = (
            f"I am interested in learning more about the **{title}** role and "
            f"how my experience in {skills_phrase} may support your team."
        )

    subject = f"Application Inquiry — {title} at {company}"

    body = f"""Dear Hiring Manager,

I am writing regarding the **{title}** opportunity at **{company}**. {fit_line}

I would welcome a brief conversation to discuss how I can contribute.

Thank you for your consideration.

Best regards,
[Your Name]
[Your Email]
[Your Phone]"""

    return f"**Subject:** {subject}\n\n{body}"
