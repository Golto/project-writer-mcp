from pathlib import Path

from app.core import (
    count_lines,
    pluralize,
    resolve_path_in_project,
    to_relative_display,
    write_bytes_atomically,
)
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import WriteFileRequest


project_storage = get_project_storage()


def write_project_file(request: WriteFileRequest) -> str:
    """Write content to a file inside a registered project.

    Creates the file if it does not exist, or overwrites it entirely if it
    does. Intermediate directories are created when create_parents is True.
    The target path must remain within the project root, outside '.git'.
    The write is atomic: an interrupted call leaves the previous content.

    Args:
        request: Project, path, content and parent creation policy.

    Returns:
        A one-line summary: created or overwritten, the line count before
        and after, the size, and the real file written through a symbolic
        link when the path designated one.

    Raises:
        PathOutsideProjectError: If the path escapes the project root.
        ProtectedPathError: If the path is inside '.git'.
        IsADirectoryError: If the path designates a directory.
        FileNotFoundError: If the parent is missing and create_parents is False.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = resolve_path_in_project(project_root, request.relative_path)
    target_display = to_relative_display(project_root, target)

    if target.is_dir():
        raise IsADirectoryError(
            f"'{request.relative_path}' is a directory. Give the path of a file inside it."
        )

    previous_line_count = count_lines(target.read_bytes()) if target.exists() else None

    if request.create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    elif not target.parent.exists():
        raise FileNotFoundError(
            f"Parent directory '{to_relative_display(project_root, target.parent)}' does not exist. "
            f"Set create_parents=true to create it automatically."
        )

    encoded = request.content.encode("utf-8")
    write_bytes_atomically(target, encoded)

    new_line_count = count_lines(encoded)
    size = pluralize(len(encoded), "byte")
    # NOTE: a path through a symbolic link writes to the link target; saying
    # so avoids a surprise when the caller later reads the requested path.
    requested_display = Path(request.relative_path).as_posix()
    via_link = "" if target_display == requested_display else f" (via '{requested_display}')"

    if previous_line_count is None:
        return f"Created '{target_display}'{via_link}: {pluralize(new_line_count, 'line')}, {size}."
    return (
        f"Overwrote '{target_display}'{via_link}: {previous_line_count} -> "
        f"{pluralize(new_line_count, 'line')}, {size}."
    )


register_tool(write_project_file, WriteFileRequest, TOOL_DESCRIPTION)
