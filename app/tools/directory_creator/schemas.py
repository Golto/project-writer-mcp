from pydantic import BaseModel, Field


class CreateDirectoryRequest(BaseModel):
    """Input schema for the create_directory tool.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Path of the directory to create, relative to the
                       project root. All intermediate parents are created
                       automatically (equivalent to mkdir -p).
        exist_ok: When True, no error is raised if the directory already
                  exists. Defaults to True.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    relative_path: str = Field(
        description="Path of the directory to create, relative to the project root (e.g. 'app/services').",
    )
    exist_ok: bool = Field(
        default=True,
        description="Succeed without error when the directory already exists.",
    )
