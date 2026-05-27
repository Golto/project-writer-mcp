from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import WriteFileRequest, WriteFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def write_project_file(request: WriteFileRequest) -> WriteFileResponse:
    """Write content to a file inside a registered project.

    Creates the file if it does not exist, or overwrites it entirely if it
    does. Intermediate directories are created when create_parents is True.
    The target path must remain within the project root.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = (project_root / request.relative_path).resolve()

    assert_within_project(project_root, target)

    is_new_file = not target.exists()

    if request.create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    elif not target.parent.exists():
        raise FileNotFoundError(
            f"Parent directory '{target.parent}' does not exist. "
            f"Set create_parents=True to create it automatically."
        )

    encoded = request.content.encode("utf-8")
    target.write_bytes(encoded)

    return WriteFileResponse(
        written_path=str(target),
        created=is_new_file,
        bytes_written=len(encoded),
    )