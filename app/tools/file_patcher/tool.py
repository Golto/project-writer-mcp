import difflib

from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import PatchFileRequest, PatchFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


def _numbered_diff(original_lines: list[str], patched_lines: list[str], path_label: str) -> str:
    """Build a unified diff with explicit 1-indexed line numbers on every line.

    Unlike raw difflib.unified_diff, which only numbers the @@ hunk header,
    this prefixes every context/removed/added line with its actual line
    number -- the original file's number for context and removed lines,
    the patched file's number for added lines. This lets a caller verify
    exactly which line numbers were touched without counting lines by hand.
    """
    matcher = difflib.SequenceMatcher(a=original_lines, b=patched_lines, autojunk=False)
    groups = matcher.get_grouped_opcodes(n=3)

    if not groups:
        return "(no textual difference)"

    out: list[str] = [f"--- {path_label} (before)", f"+++ {path_label} (after)"]

    for group in groups:
        first_op = group[0]
        last_op = group[-1]
        a_start, a_end = first_op[1], last_op[2]
        b_start, b_end = first_op[3], last_op[4]
        out.append(
            f"@@ -{a_start + 1},{a_end - a_start} +{b_start + 1},{b_end - b_start} @@"
        )
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for offset, i in enumerate(range(i1, i2)):
                    j = j1 + offset
                    out.append(f" {j + 1:>5} | {original_lines[i]}")
            else:
                if tag in ("replace", "delete"):
                    for i in range(i1, i2):
                        out.append(f"-{i + 1:>5} | {original_lines[i]}")
                if tag in ("replace", "insert"):
                    for j in range(j1, j2):
                        out.append(f"+{j + 1:>5} | {patched_lines[j]}")

    return "\n".join(out)


@mcp.tool()
def patch_project_file(request: PatchFileRequest) -> PatchFileResponse:
    """Replace a line range inside a registered project file.

    Reads the file, substitutes the specified range with new_content,
    then writes the result back. All other lines are preserved unchanged.
    The target path must remain within the project root.

    Line numbers are 1-indexed and both start_line and end_line are
    inclusive. The replacement may contain any number of lines -- it does
    not need to match the size of the replaced range.

    preview defaults to True. On the first call, the tool returns a
    numbered diff of the change without writing anything. Read the diff,
    verify that the correct lines are being replaced, then call the tool
    again with preview=False to confirm and apply the write.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = (project_root / request.relative_path).resolve()

    assert_within_project(project_root, target)

    if not target.exists():
        raise FileNotFoundError(
            f"File '{target}' does not exist. "
            f"Use write_project_file to create it first."
        )
    if target.is_dir():
        raise IsADirectoryError(f"Path '{target}' is a directory, not a file.")

    if request.start_line > request.end_line:
        raise ValueError(
            f"start_line ({request.start_line}) must be <= end_line ({request.end_line})."
        )

    original_text = target.read_text(encoding="utf-8")
    had_trailing_newline = original_text.endswith("\n")
    original_lines = original_text.splitlines()
    total_original = len(original_lines)

    # Clamp to actual file boundaries (1-indexed to 0-indexed conversion)
    start_index = request.start_line - 1
    end_index = request.end_line  # exclusive for slicing

    if start_index >= total_original:
        raise ValueError(
            f"start_line ({request.start_line}) exceeds the file length ({total_original} lines)."
        )

    end_index = min(end_index, total_original)
    replaced_count = end_index - start_index

    replacement_lines = request.new_content.splitlines()

    patched_lines = original_lines[:start_index] + replacement_lines + original_lines[end_index:]

    # Preserve the file's original trailing-newline convention instead of
    # silently stripping or adding one on every patch.
    new_text = "\n".join(patched_lines)
    if patched_lines and had_trailing_newline:
        new_text += "\n"

    diff_text = _numbered_diff(original_lines, patched_lines, request.relative_path)

    if request.preview:
        return PatchFileResponse(
            written_path=str(target),
            replaced_line_count=replaced_count,
            inserted_line_count=len(replacement_lines),
            total_lines=len(patched_lines),
            preview=True,
            message=(
                "PREVIEW ONLY -- nothing was written. "
                "Review the diff above, then call this tool again with preview=False to apply the change."
            ),
            diff=diff_text,
        )

    target.write_text(new_text, encoding="utf-8")

    return PatchFileResponse(
        written_path=str(target),
        replaced_line_count=replaced_count,
        inserted_line_count=len(replacement_lines),
        total_lines=len(patched_lines),
        preview=False,
        message=None,
        diff=diff_text,
    )
