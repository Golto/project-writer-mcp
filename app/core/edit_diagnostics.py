import difflib
import re

from .text_file import split_lines


FUZZY_MATCH_CUTOFF = 0.6
"""Minimum similarity for a block of the file to be shown as the closest match."""

MAX_FUZZY_WINDOWS = 20_000
"""Upper bound on the candidate blocks compared, to bound latency on huge files."""

MAX_SHOWN_LINES = 15
"""Longest excerpt of the file quoted in a diagnostic."""

MAX_SHOWN_LINE_LENGTH = 300
"""Longer lines are cut in quoted excerpts."""

LINE_NUMBER_PREFIX_PATTERNS = (
    # NOTE: read_project_file renders lines as ' 12 | content' with a box
    # drawing bar; a copied empty line may have lost its trailing space.
    re.compile(r"^\s*\d+ \u2502 ?"),
    # NOTE: search_project_content renders '12:match' and '12-context'.
    re.compile(r"^\d+[:-]"),
)


# ----------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------

def _quote_lines(lines: list[str], first_line_number: int) -> str:
    """Quote lines of the file with their numbers, as read_project_file shows them.

    Args:
        lines: Lines to quote.
        first_line_number: 1-indexed number of the first line.

    Returns:
        The numbered lines, cut to MAX_SHOWN_LINES lines.
    """
    shown = lines[:MAX_SHOWN_LINES]
    width = len(str(first_line_number + len(shown) - 1))
    rendered = []
    for offset, line in enumerate(shown):
        if len(line) > MAX_SHOWN_LINE_LENGTH:
            line = f"{line[:MAX_SHOWN_LINE_LENGTH]} [...]"
        rendered.append(f"{first_line_number + offset:>{width}} \u2502 {line}")
    if len(lines) > MAX_SHOWN_LINES:
        rendered.append(f"[... {len(lines) - MAX_SHOWN_LINES} more lines]")
    return "\n".join(rendered)


def _block_description(first_line_number: int, line_count: int) -> str:
    """Name a block of lines: 'line 12' or 'lines 12-15'.

    Args:
        first_line_number: 1-indexed number of the first line.
        line_count: Number of lines in the block.

    Returns:
        A short description of the block.
    """
    if line_count <= 1:
        return f"line {first_line_number}"
    return f"lines {first_line_number}-{first_line_number + line_count - 1}"


# ----------------------------------------------------------------
# Individual diagnostics
# ----------------------------------------------------------------

def _strip_line_number_prefixes(old_string: str) -> str | None:
    """Remove line-number prefixes copied from the navigator output, if any.

    Args:
        old_string: Text the caller looked for.

    Returns:
        old_string without its prefixes when every non-blank line carries
        one of the known prefixes, None otherwise.
    """
    lines = old_string.split("\n")
    for pattern in LINE_NUMBER_PREFIX_PATTERNS:
        if all(pattern.match(line) for line in lines if line.strip()):
            return "\n".join(pattern.sub("", line, count=1) for line in lines)
    return None


def _normalize_whitespace(line: str) -> str:
    """Collapse every run of whitespace, so only visible characters count."""
    return " ".join(line.split())


def _target_lines(old_string: str) -> list[str]:
    """Split old_string into lines, dropping blank lines at both ends.

    Args:
        old_string: Text the caller looked for.

    Returns:
        Its lines, without leading and trailing blank lines.
    """
    lines = split_lines(old_string)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _find_whitespace_insensitive_match(file_lines: list[str], target_lines: list[str]) -> int | None:
    """Find a block of the file equal to the target once whitespace is ignored.

    Args:
        file_lines: Lines of the file.
        target_lines: Lines of old_string, without blank ends.

    Returns:
        The 0-indexed first line of the first matching block, or None.
    """
    normalized_target = [_normalize_whitespace(line) for line in target_lines]
    normalized_file = [_normalize_whitespace(line) for line in file_lines]
    block_length = len(normalized_target)

    for start in range(len(normalized_file) - block_length + 1):
        if normalized_file[start:start + block_length] == normalized_target:
            return start
    return None


def _find_closest_block(file_lines: list[str], target_lines: list[str]) -> tuple[int, float] | None:
    """Find the block of the file most similar to the target.

    Blocks have as many lines as the target. The cheap upper bounds of
    SequenceMatcher skip most blocks before the exact ratio is computed.

    Args:
        file_lines: Lines of the file.
        target_lines: Lines of old_string, without blank ends.

    Returns:
        The 0-indexed first line of the best block and its similarity, or
        None when nothing reaches FUZZY_MATCH_CUTOFF.
    """
    block_length = len(target_lines)
    matcher = difflib.SequenceMatcher(autojunk=False)
    # NOTE: seq2 is the one SequenceMatcher preprocesses, so the fixed
    # target goes there and each candidate block goes to seq1.
    matcher.set_seq2("\n".join(target_lines))

    best_start: int | None = None
    best_ratio = FUZZY_MATCH_CUTOFF
    last_start = max(0, len(file_lines) - block_length)

    for start in range(min(last_start + 1, MAX_FUZZY_WINDOWS)):
        matcher.set_seq1("\n".join(file_lines[start:start + block_length]))
        if matcher.real_quick_ratio() <= best_ratio or matcher.quick_ratio() <= best_ratio:
            continue
        ratio = matcher.ratio()
        if ratio > best_ratio:
            best_start, best_ratio = start, ratio

    if best_start is None:
        return None
    return best_start, best_ratio


# ----------------------------------------------------------------
# Public API
# ----------------------------------------------------------------

def explain_missing_match(text: str, old_string: str) -> str:
    """Explain why old_string was not found, and show what to copy instead.

    The checks go from the most specific cause to the vaguest one:
    line-number prefixes copied from the navigator, then a whitespace or
    indentation mismatch, then the closest block of the file.

    Args:
        text: Current content of the file, as edits see it.
        old_string: Text the caller looked for.

    Returns:
        One or more sentences, possibly followed by a numbered excerpt of
        the file. Never empty.
    """
    stripped = _strip_line_number_prefixes(old_string)
    if stripped is not None and stripped != old_string:
        occurrence_count = text.count(stripped) if stripped else 0
        if occurrence_count >= 1:
            return (
                "old_string includes the line-number prefixes shown by the navigator "
                "(such as '12 \u2502 ' or '12:'). Remove them from old_string, and do not put "
                "them in new_string: without them, the text matches the file."
            )

    file_lines = split_lines(text)
    target_lines = _target_lines(old_string)
    if not target_lines:
        return "old_string only contains whitespace, which cannot locate an edit."

    whitespace_match = _find_whitespace_insensitive_match(file_lines, target_lines)
    if whitespace_match is not None:
        block = file_lines[whitespace_match:whitespace_match + len(target_lines)]
        return (
            f"old_string matches {_block_description(whitespace_match + 1, len(block))} except for "
            f"whitespace (indentation, tabs or trailing spaces). The exact text of the file is:\n"
            f"{_quote_lines(block, whitespace_match + 1)}\n"
            f"Copy it exactly into old_string, without the line numbers."
        )

    closest = _find_closest_block(file_lines, target_lines)
    if closest is not None:
        start, ratio = closest
        block = file_lines[start:start + len(target_lines)]
        return (
            f"The closest text is at {_block_description(start + 1, len(block))} "
            f"({round(ratio * 100)}% similar):\n"
            f"{_quote_lines(block, start + 1)}\n"
            f"If this is the intended place, copy it exactly into old_string, without the line numbers. "
            f"Otherwise, read the file again: it may have changed since it was last read."
        )

    return (
        "Nothing similar was found in the file. Read the file again: it may have changed "
        "since it was last read, or the edit may target another file."
    )
