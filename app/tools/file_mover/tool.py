from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import MoveFileRequest, MoveFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def move_file(request: MoveFileRequest) -> MoveFileResponse:
    """Move or rename a file inside a registered project.

    Both source and destination must remain within the project root.
    Raises an error if the source does not exist or if the destination
    already exists and overwrite is False.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    source = (project_root / request.source_path).resolve()
    destination = (project_root / request.destination_path).resolve()

    assert_within_project(project_root, source)
    assert_within_project(project_root, destination)

    if not source.exists():
        raise FileNotFoundError(f"Source file '{source}' does not exist.")

    if source.is_dir():
        raise IsADirectoryError(
            f"Source '{source}' is a directory. This tool only moves individual files."
        )

    destination_existed = destination.exists()

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