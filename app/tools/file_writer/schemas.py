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

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    relative_path: str = Field(
        description="Path to the target file relative to the project root (e.g. 'app/core/utils.py').",
    )
    content: str = Field(description="Complete content of the file. Any existing content is replaced.")
    create_parents: bool = Field(
        default=True,
        description="Create missing intermediate directories automatically.",
    )
