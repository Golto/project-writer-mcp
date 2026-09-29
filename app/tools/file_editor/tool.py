from app.core import (
    TextEdit,
    apply_edits,
    build_not_found_message,
    count_lines,
    decode_text_file,
    encode_text_file,
    format_numbered_diff,
    pluralize,
    resolve_path_in_project,
    to_relative_display,
    write_bytes_atomically,
)
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import EditFileRequest


project_storage = get_project_storage()


def edit_project_file(request: EditFileRequest) -> str:
    """Replace exact text in an existing file of a registered project.

    Every edit is applied in memory first; the file is written atomically
    only once all of them succeeded, so a failing edit never leaves a
    half-edited file. Line endings and the final newline are preserved.

    Args:
        request: Project, file path and the ordered list of edits.

    Returns:
        A summary line (edits, replacements, line count before and after)
        followed by a numbered diff using the new line numbers.

    Raises:
        PathOutsideProjectError: If the path escapes the project root.
        ProtectedPathError: If the path is inside '.git'.
        FileNotFoundError: If the file does not exist. The message suggests
                           similar paths.
        IsADirectoryError: If the path designates a directory.
        BinaryFileError: If the file looks binary.
        NotUtf8Error: If the file is not valid UTF-8.
        EditError: If an edit cannot be applied. The message says which edit,
                   why, and quotes the closest text of the file.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = resolve_path_in_project(project_root, request.relative_path)
    target_display = to_relative_display(project_root, target)

    if not target.exists():
        raise FileNotFoundError(
            f"{build_not_found_message(project_root, request.relative_path)} "
            f"To create a new file, use write_project_file."
        )
    if target.is_dir():
        raise IsADirectoryError(f"'{target_display}' is a directory, not a file.")

    raw_content = target.read_bytes()
    text_file = decode_text_file(raw_content, target_display)

    edits = [
        TextEdit(old_string=spec.old_string, new_string=spec.new_string, replace_all=spec.replace_all)
        for spec in request.to_edit_specs()
    ]
    result = apply_edits(text_file.text, edits, target_display)

    new_content = encode_text_file(result.text, text_file.uses_crlf)
    write_bytes_atomically(target, new_content)

    summary = f"Edited '{target_display}': {pluralize(len(edits), 'edit')}"
    if result.replacement_count != len(edits):
        summary += f" ({pluralize(result.replacement_count, 'replacement')})"
    summary += f", {count_lines(raw_content)} -> {pluralize(count_lines(new_content), 'line')}."

    return f"{summary}\n{format_numbered_diff(text_file.text, result.text)}"


register_tool(edit_project_file, EditFileRequest, TOOL_DESCRIPTION)
