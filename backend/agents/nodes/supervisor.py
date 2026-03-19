"""Supervisor node: merge, deduplicate, rank, and summarize findings."""

from agents.state import ReviewState


def supervisor_node(state: ReviewState) -> dict:
    """Merge findings from all agents, deduplicate, rank, and generate summary.

    Writes to `deduplicated_findings` (not `findings`) to avoid the accumulator
    reducer from appending back the deduplicated list to the raw agent findings.
    """
    findings = state.get("findings", [])

    # Deduplicate: same file + same line + similar title
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f["file_path"], f.get("line_number"), f["title"][:50].lower())
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    # Sort by severity (high first), then confidence
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    unique_findings.sort(
        key=lambda f: (severity_order.get(f["severity"], 4), -f.get("confidence", 0))
    )

    # Count severities
    severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    for f in unique_findings:
        sev = f.get("severity", "info")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Build summary
    total = len(unique_findings)
    affected_files = len(set(f["file_path"] for f in unique_findings))
    agents_used = len(set(f["agent_role"] for f in unique_findings))

    summary_parts = [
        f"**{total} issues** found across **{affected_files} files** by **{agents_used} agents**.",
    ]
    if severity_counts["high"] > 0:
        summary_parts.append(f"- {severity_counts['high']} HIGH severity issues requiring immediate attention")
    if severity_counts["medium"] > 0:
        summary_parts.append(f"- {severity_counts['medium']} MEDIUM severity issues to address")
    if severity_counts["low"] > 0:
        summary_parts.append(f"- {severity_counts['low']} LOW severity suggestions")

    summary = "\n".join(summary_parts)

    return {
        "deduplicated_findings": unique_findings,
        "summary": summary,
        "severity_counts": severity_counts,
    }
