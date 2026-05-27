from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import DeleteFileRequest, DeleteFileResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def delete_file(request: DeleteFileRequest) -> DeleteFileResponse:
    """Delete a file from a registered project.

    Raises an error if the path is a directory -- this tool only deletes
    individual files. The target path must remain within the project root.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = (project_root / request.relative_path).resolve()

    assert_within_project(project_root, target)

    if not target.exists():
        if request.allow_missing:
            return DeleteFileResponse(deleted_path=str(target), deleted=False)
        raise FileNotFoundError(
            f"File '{target}' does not exist. "
            f"Set allow_missing=True to suppress this error."
        )

    if target.is_dir():
        raise IsADirectoryError(
            f"Path '{target}' is a directory. "
            f"This tool only deletes individual files."
        )

    target.unlink()

    return DeleteFileResponse(deleted_path=str(target), deleted=True)