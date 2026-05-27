from pydantic import BaseModel, Field


class PatchFileRequest(BaseModel):
    """Input schema for the patch_project_file tool.

    Replaces a contiguous range of lines in an existing file with new
    content, leaving all other lines untouched. Line numbers are 1-indexed.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Path to the target file relative to the project root.
        start_line: First line to replace, 1-indexed, inclusive.
        end_line: Last line to replace, 1-indexed, inclusive.
        new_content: Replacement text for the specified line range.
                     May contain a different number of lines than the
                     range being replaced.
    """

    project_id: str = Field(description="Registered project identifier.")
    relative_path: str = Field(
        description="Path to the target file relative to the project root."
    )
    start_line: int = Field(
        ge=1,
        description="First line to replace, 1-indexed inclusive.",
    )
    end_line: int = Field(
        ge=1,
        description="Last line to replace, 1-indexed inclusive.",
    )
    new_content: str = Field(
        description="Replacement content for the specified line range."
    )


class PatchFileResponse(BaseModel):
    """Output schema for the patch_project_file tool.

    Attributes:
        written_path: Absolute path of the patched file.
        replaced_line_count: Number of original lines that were removed.
        inserted_line_count: Number of new lines that were inserted.
        total_lines: Total number of lines in the file after patching.
    """

    written_path: str = Field(description="Absolute path of the patched file.")
    replaced_line_count: int = Field(description="Number of original lines removed.")
    inserted_line_count: int = Field(description="Number of new lines inserted.")
    total_lines: int = Field(description="Total lines in the file after patching.")