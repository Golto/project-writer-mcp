from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import resolve_path_in_project
from app.core.pruning import collect_empty_directories

from .schemas import PruneEmptyDirectoriesRequest, PruneEmptyDirectoriesResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def prune_empty_directories(request: PruneEmptyDirectoriesRequest) -> PruneEmptyDirectoriesResponse:
    """Remove all empty directories under a registered project path.

    Walks the target tree bottom-up so that directories emptied by the
    removal of their own children are caught in the same pass. The target
    root itself is never removed -- only its descendants.

    Hidden directories (names starting with '.') are skipped by default.
    Set include_hidden=True to include them in the sweep. '.git' is never
    swept, whatever include_hidden says.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    if request.relative_path is not None:
        prune_root = resolve_path_in_project(project_root, request.relative_path)
    else:
        prune_root = project_root

    if not prune_root.exists():
        raise FileNotFoundError(f"Directory '{prune_root}' does not exist.")
    if not prune_root.is_dir():
        raise NotADirectoryError(f"Path '{prune_root}' is not a directory.")

    empty_directories = collect_empty_directories(prune_root, request.include_hidden)

    for directory in empty_directories:
        directory.rmdir()

    return PruneEmptyDirectoriesResponse(
        root_path=str(prune_root),
        removed_directories=[str(directory) for directory in empty_directories],
        removed_count=len(empty_directories),
    )
