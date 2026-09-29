from app.core import build_not_found_message, resolve_entry_in_project, to_relative_display
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import DeleteFileRequest


project_storage = get_project_storage()


def delete_file(request: DeleteFileRequest) -> str:
    """Delete a file from a registered project.

    Raises an error if the path is a directory -- this tool only deletes
    individual files. The target path must remain within the project root,
    outside '.git'. A symbolic link is deleted itself, never its target.

    Args:
        request: Project, file path and missing-file policy.

    Returns:
        A one-line summary of what was deleted, or why nothing was.

    Raises:
        PathOutsideProjectError: If the path escapes the project root.
        ProtectedPathError: If the path is inside '.git'.
        FileNotFoundError: If the file does not exist and allow_missing is
                           False. The message suggests similar paths.
        IsADirectoryError: If the path designates a directory.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = resolve_entry_in_project(project_root, request.relative_path)
    target_display = to_relative_display(project_root, target)

    # NOTE: exists() follows symlinks, so a broken link would look missing.
    is_link = target.is_symlink()

    if not (is_link or target.exists()):
        if request.allow_missing:
            return f"Nothing to delete: '{target_display}' does not exist."
        raise FileNotFoundError(
            f"{build_not_found_message(project_root, request.relative_path)} "
            f"Set allow_missing=true to ignore missing files."
        )

    if target.is_dir() and not is_link:
        raise IsADirectoryError(
            f"'{target_display}' is a directory: this tool only deletes files. "
            f"Use prune_empty_directories to remove directories once empty."
        )

    target.unlink()

    if is_link:
        return f"Deleted the symbolic link '{target_display}' (its target was left untouched)."
    return f"Deleted '{target_display}'."


register_tool(delete_file, DeleteFileRequest, TOOL_DESCRIPTION)
