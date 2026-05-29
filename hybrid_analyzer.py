"""Hybrid local scoring for Adzuna job listings (Find Jobs tab)."""

import re

SKILL_KEYWORDS = [
    "product management", "product owner", "product strategy", "roadmap", "backlog",
    "user stories", "stakeholders", "stakeholder management", "agile", "scrum",
    "jira", "confluence", "ai", "llm", "rag", "nlp", "langchain", "machine learning",
    "prompt engineering", "automation", "analytics", "apis", "sql", "python", "aws",
    "saas", "b2b", "prd", "mvp", "go-to-market", "kanban", "react", "docker",
]
SKILLS_BY_LENGTH = sorted(set(SKILL_KEYWORDS), key=len, reverse=True)
PRIORITY_WEIGHTS = {
    "ai": 4.0, "product management": 4.0, "llm": 3.5, "roadmap": 3.5,
    "agile": 3.0, "stakeholders": 3.0, "prompt engineering": 3.5,
    "apis": 3.0, "analytics": 3.0, "automation": 3.0,
}
SEMANTIC_GROUPS = {
    "ai_llm": {"skills": {"ai", "llm", "rag", "nlp", "langchain", "machine learning", "automation"}, "phrases": ["embeddings", "semantic search", "agentic ai"]},
    "product": {"skills": {"product management", "roadmap", "backlog", "user stories", "product owner"}, "phrases": []},
    "delivery": {"skills": {"agile", "scrum", "jira", "stakeholder management", "stakeholders"}, "phrases": ["safe", "scaled agile"]},
    "data_api": {"skills": {"sql", "apis", "analytics"}, "phrases": ["reporting", "data workflows"]},
    "domain": {"skills": {"saas", "b2b"}, "phrases": ["banking", "financial services", "staffing", "recruiting", "workflow automation"]},
}
PM_TITLES = ["product manager", "technical product manager", "ai product manager", "product owner", "business analyst"]
INTERN = ["intern", "internship", "co-op"]
EXEC = ["director", "vp ", "vice president", "head of"]
WEIGHTS = (0.40, 0.25, 0.20, 0.10, 0.05)


def get_match_label(pct: int, is_intern: bool = False) -> str:
    if is_intern:
        return "Low match"
    if pct >= 80:
        return "Strong match"
    if pct >= 60:
        return "Good match"
    if pct >= 40:
        return "Moderate match"
    return "Low match"


def analyze_match(
    resume: str,
    job_description: str,
    job_title: str = "",
    contract_type: str = "",
    contract_time: str = "",
    employment_preference: str = "Both",
) -> dict:
    rn, jd = resume.lower(), job_description.lower()
    combined = f"{job_title.lower()} {jd}".strip()
    r_sk, j_sk = _skills(resume), _skills(job_description)
    match, miss = r_sk & j_sk, j_sk - r_sk
    r_sig, j_sig = _signals(rn), _signals(combined)
    is_intern = j_sig["intern"]

    s = _skill_score(rn, combined, r_sk, j_sk, match)
    ro = _role_score(rn, r_sig, j_sig, job_title.lower())
    se = _seniority_score(r_sig, j_sig)
    do = _domain_score(rn, combined, r_sk, j_sk)
    em = _employment_score(contract_type, contract_time, employment_preference)

    final = WEIGHTS[0] * s + WEIGHTS[1] * ro + WEIGHTS[2] * se + WEIGHTS[3] * do + WEIGHTS[4] * em
    if not match and ro >= 55:
        final = max(final, min(35, 20 + ro * 0.12))
    if ro < 25 and s < 15 and do < 20 and not match:
        final = 0
    if is_intern and not r_sig["intern"]:
        final = min(final, 28)
    if len(match) <= 1:
        final = min(final, 42)
    elif len(match) == 2:
        final = min(final, 55)

    pct = round(max(0, min(100, final)))
    label = get_match_label(pct, is_intern)
    m_disp = sorted(match, key=lambda x: PRIORITY_WEIGHTS.get(x, 1), reverse=True)
    return {
        "match_percent": pct,
        "match_label": label,
        "is_internship": is_intern,
        "matching_skills": [x.title() if x != "ai" else "AI" for x in m_disp],
        "missing_skills": [x.title() for x in sorted(miss)],
        "professional_summary": f"Hybrid score **{pct}%** ({label.lower()}).",
        "score_breakdown": {"skills": round(s), "role": round(ro), "seniority": round(se), "domain": round(do), "employment": round(em)},
    }


def _skills(text: str) -> set:
    t = text.lower()
    found = set()
    for sk in SKILLS_BY_LENGTH:
        if " " in sk or "/" in sk:
            if sk in t:
                found.add(sk)
        elif re.search(rf"(?<![a-z0-9]){re.escape(sk)}(?![a-z0-9])", t):
            found.add(sk)
    return found


def _signals(text: str) -> dict:
    return {
        "intern": any(p in text for p in INTERN),
        "exec": any(p in text for p in EXEC),
        "pm": any(p in text for p in PM_TITLES),
        "senior": bool(re.search(r"\bsenior\b", text)),
    }


def _group_hit(text: str, skills: set, group: dict) -> bool:
    return bool(skills & group["skills"]) or any(p in text for p in group["phrases"])


def _skill_score(rt, jt, rs, js, match) -> float:
    if not js:
        return 50.0
    kw = sum(PRIORITY_WEIGHTS.get(s, 1) for s in match) / sum(PRIORITY_WEIGHTS.get(s, 1) for s in js) * 100
    groups = sum(1 for g in SEMANTIC_GROUPS.values() if _group_hit(jt, js, g))
    gm = sum(1 for g in SEMANTIC_GROUPS.values() if _group_hit(jt, js, g) and _group_hit(rt, rs, g))
    gr = (gm / groups * 100) if groups else 50
    return min(kw * 0.65 + gr * 0.35, 58) if len(match) <= 2 else kw * 0.65 + gr * 0.35


def _role_score(rt, rs, js, title) -> float:
    if js["intern"]:
        return 12.0 if rs["pm"] or rs["senior"] else 25.0
    if (js["pm"] or any(p in title for p in PM_TITLES)) and rs["pm"]:
        return 92.0
    if js["exec"] and rs["pm"]:
        return 58.0
    tw = {w for w in re.findall(r"[a-z]{3,}", title) if w not in {"and", "the", "for"}}
    if tw:
        return 35 + len(tw & set(re.findall(r"[a-z]{3,}", rt))) / len(tw) * 55
    return 40.0


def _level(sig) -> int:
    if sig["intern"]:
        return 1
    if sig["exec"]:
        return 6
    if sig["senior"]:
        return 4
    if sig["pm"]:
        return 3
    return 3


def _seniority_score(rs, js) -> float:
    gap = abs(_level(rs) - _level(js))
    if gap == 0:
        return 95.0
    if gap == 1:
        return 72.0
    if _level(rs) >= 4 and _level(js) == 1:
        return 8.0
    return 25.0 if gap >= 2 else 48.0


def _domain_score(rt, jt, rs, js) -> float:
    g = SEMANTIC_GROUPS["domain"]
    if not _group_hit(jt, js, g):
        return 55.0
    return 88.0 if _group_hit(rt, rs, g) else 22.0


def _employment_score(ct, ctime, pref) -> float:
    c, t = (ct or "").lower(), (ctime or "").lower()
    if pref == "Contract":
        return 95.0 if c == "contract" else 50.0
    if pref == "Full Time":
        return 95.0 if t == "full_time" and c != "contract" else 55.0
    return 80.0 if c == "contract" or t == "full_time" else 60.0
