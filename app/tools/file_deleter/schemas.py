from pydantic import BaseModel, Field


class DeleteFileRequest(BaseModel):
    """Input schema for the delete_file tool.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Path to the file to delete, relative to the project root.
        allow_missing: When True, no error is raised if the file does not exist.
                       Useful for idempotent cleanup workflows. Defaults to False.
    """

    project_id: str = Field(description="Registered project identifier.")
    relative_path: str = Field(
        description="Path to the file to delete, relative to the project root."
    )
    allow_missing: bool = Field(
        default=False,
        description="Suppress errors when the file does not exist.",
    )


class DeleteFileResponse(BaseModel):
    """Output schema for the delete_file tool.

    Attributes:
        deleted_path: Absolute path of the file that was deleted.
        deleted: True if the file existed and was removed. False if
                 allow_missing was True and the file was already absent.
    """

    deleted_path: str = Field(description="Absolute path of the targeted file.")
    deleted: bool = Field(description="True if the file was actually removed.")