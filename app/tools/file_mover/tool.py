from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import resolve_entry_in_project

from .schemas import MoveFileRequest, MoveFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def move_file(request: MoveFileRequest) -> MoveFileResponse:
    """Move or rename a file inside a registered project.

    Both source and destination must remain within the project root.
    Raises an error if the source does not exist or if the destination
    already exists and overwrite is False. A symbolic link is moved itself,
    never its target; a relative link may no longer resolve once moved.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    source = resolve_entry_in_project(project_root, request.source_path)
    destination = resolve_entry_in_project(project_root, request.destination_path)

    # NOTE: exists() follows symlinks, so a broken link would look missing.
    source_is_link = source.is_symlink()

    if not (source_is_link or source.exists()):
        raise FileNotFoundError(f"Source file '{source}' does not exist.")

    if source.is_dir() and not source_is_link:
        raise IsADirectoryError(
            f"Source '{source}' is a directory. This tool only moves individual files."
        )

    destination_existed = destination.is_symlink() or destination.exists()

    if destination_existed and not request.overwrite:
        raise FileExistsError(
            f"Destination '{destination}' already exists. "
            f"Set overwrite=True to replace it."
        )

    if request.create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    elif not destination.parent.exists():
        raise FileNotFoundError(
            f"Destination directory '{destination.parent}' does not exist. "
            f"Set create_parents=True to create it automatically."
        )

    source.rename(destination)

    return MoveFileResponse(
        source_path=str(source),
        destination_path=str(destination),
        overwritten=destination_existed,
    )
