from pydantic import BaseModel, Field


class DeleteFileRequest(BaseModel):
    """Input schema for the delete_file tool.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Path to the file to delete, relative to the project root.
        allow_missing: When True, no error is raised if the file does not exist.
                       Useful for idempotent cleanup workflows. Defaults to False.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    relative_path: str = Field(
        description="Path to the file to delete, relative to the project root.",
    )
    allow_missing: bool = Field(
        default=False,
        description="Succeed without error when the file does not exist.",
    )
