"""Node: Fetch and prepare PR diff for review agents, with large PR chunking."""

from agents.state import ReviewState
from app.services.chunker import chunk_pr_diff


# Files to skip during review
SKIP_PATTERNS = {
    ".lock", ".sum", ".mod", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", ".min.js", ".min.css", ".map",
    ".svg", ".png", ".jpg", ".gif", ".ico", ".woff", ".woff2",
}


def fetch_diff_node(state: ReviewState) -> dict:
    """Transform raw PR diff into structured file data for agents.

    For large PRs (>800 lines of diff), chunks files into manageable groups.
    The pipeline runs once per chunk, and findings are merged by the supervisor.
    """
    pr_diff = state["pr_diff"]
    files = pr_diff.get("files", [])

    # Filter out non-reviewable files
    reviewable_files = []
    for f in files:
        filename = f["filename"]
        if any(filename.endswith(pat) for pat in SKIP_PATTERNS):
            continue
        if not f.get("patch"):
            continue
        reviewable_files.append(f)

    # Chunk large PRs
    chunks = chunk_pr_diff(reviewable_files)

    if len(chunks) <= 1:
        return {"files": reviewable_files}

    # For multi-chunk PRs, flatten all files but add chunk metadata
    # The review agents will see chunk context in their prompts
    for chunk in chunks:
        for f in chunk.files:
            f["_chunk"] = f"{chunk.chunk_index + 1}/{chunk.total_chunks}"

    all_files = [f for chunk in chunks for f in chunk.files]
    return {"files": all_files}
