from app.core import pluralize, resolve_path_in_project, to_relative_display
from app.core.pruning import collect_empty_directories
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import PruneEmptyDirectoriesRequest


project_storage = get_project_storage()

MAX_LISTED_DIRECTORIES = 50
"""The reply lists removed directories up to this count, then only counts them."""


def prune_empty_directories(request: PruneEmptyDirectoriesRequest) -> str:
    """Remove all empty directories under a registered project path.

    Walks the target tree bottom-up so that directories emptied by the
    removal of their own children are caught in the same pass. The target
    root itself is never removed -- only its descendants.

    Hidden directories (names starting with '.') are skipped by default.
    Set include_hidden=True to include them in the sweep. '.git' is never
    swept, whatever include_hidden says.

    Args:
        request: Project, starting directory and hidden-directory policy.

    Returns:
        A summary giving the number of removed directories and listing them,
        deepest first.

    Raises:
        PathOutsideProjectError: If the path escapes the project root.
        ProtectedPathError: If the path is inside '.git'.
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path designates a file.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    if request.relative_path is not None:
        prune_root = resolve_path_in_project(project_root, request.relative_path)
    else:
        prune_root = project_root
    root_display = to_relative_display(project_root, prune_root)

    if not prune_root.exists():
        raise FileNotFoundError(f"Directory not found: '{request.relative_path}'.")
    if not prune_root.is_dir():
        raise NotADirectoryError(f"'{root_display}' is a file, not a directory.")

    empty_directories = collect_empty_directories(prune_root, request.include_hidden)

    for directory in empty_directories:
        directory.rmdir()

    location = "the project" if root_display == "." else f"'{root_display}'"
    if not empty_directories:
        return f"No empty directory found under {location}."

    removed = [to_relative_display(project_root, directory) for directory in empty_directories]
    listed = ", ".join(removed[:MAX_LISTED_DIRECTORIES])
    if len(removed) > MAX_LISTED_DIRECTORIES:
        listed += f", and {len(removed) - MAX_LISTED_DIRECTORIES} more"
    return f"Removed {pluralize(len(removed), 'empty directory', 'empty directories')} under {location}: {listed}."


register_tool(prune_empty_directories, PruneEmptyDirectoriesRequest, TOOL_DESCRIPTION)
