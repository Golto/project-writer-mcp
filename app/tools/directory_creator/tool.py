from app.core import resolve_path_in_project, to_relative_display
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import CreateDirectoryRequest


project_storage = get_project_storage()


def create_directory(request: CreateDirectoryRequest) -> str:
    """Create a directory (and all missing parents) inside a registered project.

    Behaves like `mkdir -p`. The target path must remain within the
    project root, outside '.git'.

    Args:
        request: Project, directory path and existing-directory policy.

    Returns:
        A one-line summary saying whether the directory was created.

    Raises:
        PathOutsideProjectError: If the path escapes the project root.
        ProtectedPathError: If the path is inside '.git'.
        FileExistsError: If the path is an existing file, or an existing
                         directory while exist_ok is False.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = resolve_path_in_project(project_root, request.relative_path)
    target_display = to_relative_display(project_root, target)

    if target.exists() and not target.is_dir():
        raise FileExistsError(f"'{target_display}' already exists and is a file, not a directory.")

    if target.exists():
        if not request.exist_ok:
            raise FileExistsError(
                f"Directory '{target_display}' already exists. Set exist_ok=true to accept it."
            )
        return f"Directory '{target_display}' already exists, nothing to do."

    target.mkdir(parents=True)
    return f"Created directory '{target_display}'."


register_tool(create_directory, CreateDirectoryRequest, TOOL_DESCRIPTION)
