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

    project_id: str = Field(description="Registered project identifier.")
    relative_path: str = Field(
        description="Path of the directory to create, relative to the project root."
    )
    exist_ok: bool = Field(
        default=True,
        description="Suppress errors when the directory already exists.",
    )


class CreateDirectoryResponse(BaseModel):
    """Output schema for the create_directory tool.

    Attributes:
        created_path: Absolute path of the directory.
        created: True if the directory was newly created. False if it
                 already existed and exist_ok was True.
    """

    created_path: str = Field(description="Absolute path of the directory.")
    created: bool = Field(description="True if the directory was newly created.")