from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import resolve_path_in_project, write_bytes_atomically

from .schemas import WriteFileRequest, WriteFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def write_project_file(request: WriteFileRequest) -> WriteFileResponse:
    """Write content to a file inside a registered project.

    Creates the file if it does not exist, or overwrites it entirely if it
    does. Intermediate directories are created when create_parents is True.
    The target path must remain within the project root, outside '.git'.
    The write is atomic: an interrupted call leaves the previous content.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = resolve_path_in_project(project_root, request.relative_path)

    if target.is_dir():
        raise IsADirectoryError(
            f"'{request.relative_path}' is a directory. Give the path of a file inside it."
        )

    is_new_file = not target.exists()

    if request.create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    elif not target.parent.exists():
        raise FileNotFoundError(
            f"Parent directory '{target.parent}' does not exist. "
            f"Set create_parents=True to create it automatically."
        )

    encoded = request.content.encode("utf-8")
    write_bytes_atomically(target, encoded)

    return WriteFileResponse(
        written_path=str(target),
        created=is_new_file,
        bytes_written=len(encoded),
    )
