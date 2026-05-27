from pydantic import BaseModel, Field


class WriteFileRequest(BaseModel):
    """Input schema for the write_project_file tool.

    Attributes:
        project_id: Identifier of the registered project to write into.
        relative_path: Path to the target file relative to the project root.
        content: Full content to write. Overwrites any existing file.
        create_parents: When True, missing intermediate directories are
                        created automatically. Defaults to True.
    """

    project_id: str = Field(description="Registered project identifier.")
    relative_path: str = Field(
        description="Path to the target file relative to the project root (e.g. 'app/core/utils.py')."
    )
    content: str = Field(description="Full content to write to the file.")
    create_parents: bool = Field(
        default=True,
        description="Create missing intermediate directories automatically.",
    )


class WriteFileResponse(BaseModel):
    """Output schema for the write_project_file tool.

    Attributes:
        written_path: Absolute path of the file that was written.
        created: True if the file did not exist before this call.
        bytes_written: Number of bytes written to the file.
    """

    written_path: str = Field(description="Absolute path of the written file.")
    created: bool = Field(description="True if the file was newly created.")
    bytes_written: int = Field(description="Number of bytes written.")