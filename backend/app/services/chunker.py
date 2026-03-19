"""Large PR chunking service.

Splits PRs with >1000 lines of diff into manageable chunks for review agents.
Each chunk is reviewed independently, findings are merged by the supervisor.
"""

from dataclasses import dataclass


@dataclass
class DiffChunk:
    """A chunk of files from a PR diff, sized for a single LLM context."""
    chunk_index: int
    total_chunks: int
    files: list[dict]
    total_lines: int


# Target ~800 lines of diff per chunk (leave room for prompts + output)
MAX_LINES_PER_CHUNK = 800
# Max files per chunk to maintain context coherence
MAX_FILES_PER_CHUNK = 15


def chunk_pr_diff(files: list[dict], max_lines: int = MAX_LINES_PER_CHUNK) -> list[DiffChunk]:
    """Split a list of file diffs into appropriately sized chunks.

    Strategy:
    1. Sort files by size (largest first) to pack efficiently
    2. Bin-pack files into chunks, respecting line limits
    3. Keep related files together when possible (same directory)
    """
    if not files:
        return []

    # Calculate line counts for each file
    file_sizes = []
    for f in files:
        patch = f.get("patch", "")
        lines = len(patch.split("\n")) if patch else 0
        file_sizes.append((f, lines))

    # If total is under limit, return single chunk
    total_lines = sum(s for _, s in file_sizes)
    if total_lines <= max_lines:
        return [DiffChunk(chunk_index=0, total_chunks=1, files=files, total_lines=total_lines)]

    # Sort by directory then size for grouping related files
    file_sizes.sort(key=lambda x: (x[0].get("filename", "").rsplit("/", 1)[0], -x[1]))

    chunks: list[DiffChunk] = []
    current_files: list[dict] = []
    current_lines = 0

    for file_data, lines in file_sizes:
        # Single file exceeds limit — it gets its own chunk
        if lines > max_lines:
            if current_files:
                chunks.append(DiffChunk(
                    chunk_index=len(chunks), total_chunks=0,
                    files=current_files, total_lines=current_lines,
                ))
                current_files = []
                current_lines = 0
            chunks.append(DiffChunk(
                chunk_index=len(chunks), total_chunks=0,
                files=[file_data], total_lines=lines,
            ))
            continue

        # Would exceed limit — start new chunk
        if current_lines + lines > max_lines or len(current_files) >= MAX_FILES_PER_CHUNK:
            if current_files:
                chunks.append(DiffChunk(
                    chunk_index=len(chunks), total_chunks=0,
                    files=current_files, total_lines=current_lines,
                ))
            current_files = [file_data]
            current_lines = lines
        else:
            current_files.append(file_data)
            current_lines += lines

    # Last chunk
    if current_files:
        chunks.append(DiffChunk(
            chunk_index=len(chunks), total_chunks=0,
            files=current_files, total_lines=current_lines,
        ))

    # Set total_chunks on all
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    return chunks
