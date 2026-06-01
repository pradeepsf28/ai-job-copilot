from datetime import datetime

def generate_report(jobs):

    report = []

    report.append("AI JOB COPILOT REPORT")
    report.append("=" * 50)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    report.append(f"Jobs Found: {len(jobs)}")
    report.append("")

    for i, job in enumerate(jobs[:10], start=1):

        report.append(f"{i}. {job.get('title', 'N/A')}")
        report.append(f"   Company: {job.get('company', 'N/A')}")
        report.append(f"   Match Score: {job.get('match_score', 'N/A')}%")
        report.append("")

    return "\n".join(report)
