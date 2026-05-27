from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import assert_within_project

from .schemas import CreateDirectoryRequest, CreateDirectoryResponse

mcp = get_mcp()
project_storage = get_project_storage()


@mcp.tool()
def create_directory(request: CreateDirectoryRequest) -> CreateDirectoryResponse:
    """Create a directory (and all missing parents) inside a registered project.

    Behaves like `mkdir -p`. The target path must remain within the
    project root.
    """
    project_root = project_storage.resolve_project_path(request.project_id)
    target = (project_root / request.relative_path).resolve()

    assert_within_project(project_root, target)

    already_exists = target.exists()

    if already_exists and not request.exist_ok:
        raise FileExistsError(
            f"Directory '{target}' already exists. "
            f"Set exist_ok=True to suppress this error."
        )

    target.mkdir(parents=True, exist_ok=request.exist_ok)

    return CreateDirectoryResponse(
        created_path=str(target),
        created=not already_exists,
    )