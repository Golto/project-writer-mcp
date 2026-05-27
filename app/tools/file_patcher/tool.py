from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import PatchFileRequest, PatchFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def patch_project_file(request: PatchFileRequest) -> PatchFileResponse:
    """Replace a line range inside a registered project file.

    Reads the file, substitutes the specified range with new_content,
    then writes the result back. All other lines are preserved unchanged.
    The target path must remain within the project root.

    Line numbers are 1-indexed and both start_line and end_line are
    inclusive. The replacement may contain any number of lines -- it does
    not need to match the size of the replaced range.
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

    original_lines = target.read_text(encoding="utf-8").splitlines()
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

    target.write_text("\n".join(patched_lines), encoding="utf-8")

    return PatchFileResponse(
        written_path=str(target),
        replaced_line_count=replaced_count,
        inserted_line_count=len(replacement_lines),
        total_lines=len(patched_lines),
    )