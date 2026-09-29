import difflib

from .text_file import split_lines


CONTEXT_LINES = 2
"""Unchanged lines shown around each change."""

MAX_DIFF_LINES = 200
"""Longest diff returned; beyond, the model is invited to read the file."""

MAX_DIFF_LINE_LENGTH = 300
"""Longer lines are cut in the diff."""


def _cut(line: str) -> str:
    """Cut an overly long line for display."""
    if len(line) > MAX_DIFF_LINE_LENGTH:
        return f"{line[:MAX_DIFF_LINE_LENGTH]} [...]"
    return line


def format_numbered_diff(old_text: str, new_text: str) -> str:
    """Render the changes between two texts with the NEW line numbers.

    Context and added lines carry their number in the edited file, which is
    what the caller needs for any later read or edit. Removed lines have no
    number, since they no longer exist:

        @@ lines 40-43 @@
           40   def total(self):
        -           return 1
        +  41       return 2
           42

    Args:
        old_text: Content before the edits.
        new_text: Content after the edits.

    Returns:
        The hunks, or a short note when the texts are identical. Cut to
        MAX_DIFF_LINES lines, with a final note when cut.
    """
    old_lines = split_lines(old_text)
    new_lines = split_lines(new_text)
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    groups = list(matcher.get_grouped_opcodes(n=CONTEXT_LINES))

    if not groups:
        return "(no line changed)"

    width = len(str(max(len(new_lines), 1)))
    blank_number = " " * width
    rendered: list[str] = []

    for group in groups:
        first_new, last_new = group[0][3], group[-1][4]
        header_end = max(first_new + 1, last_new)
        rendered.append(f"@@ lines {first_new + 1}-{header_end} @@")

        for tag, old_start, old_end, new_start, new_end in group:
            if tag == "equal":
                for index in range(new_start, new_end):
                    rendered.append(f" {index + 1:>{width}}  {_cut(new_lines[index])}")
                continue
            for index in range(old_start, old_end):
                rendered.append(f"-{blank_number}  {_cut(old_lines[index])}")
            for index in range(new_start, new_end):
                rendered.append(f"+{index + 1:>{width}}  {_cut(new_lines[index])}")

    if len(rendered) > MAX_DIFF_LINES:
        hidden = len(rendered) - MAX_DIFF_LINES
        rendered = rendered[:MAX_DIFF_LINES]
        rendered.append(f"[Diff cut: {hidden} more lines. Read the file to check the rest.]")

    return "\n".join(rendered)
