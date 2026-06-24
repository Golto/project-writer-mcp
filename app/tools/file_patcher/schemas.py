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
        preview: When True, no write happens. Returns a unified diff of
                 the change instead so the caller can verify it first.
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
    preview: bool = Field(
        default=True,
        description=(
            "If True (default), do not write anything. Instead return a unified diff "
            "showing exactly what would change, with line numbers, so the "
            "edit can be verified before it is applied for real. "
            "Set to False only after reviewing the diff and confirming the patch is correct."
        ),
    )


class PatchFileResponse(BaseModel):
    """Output schema for the patch_project_file tool.

    Attributes:
        written_path: Absolute path of the patched file.
        replaced_line_count: Number of original lines that were removed.
        inserted_line_count: Number of new lines that were inserted.
        total_lines: Total number of lines in the file after patching.
        preview: Whether this response is a preview (no write occurred).
        diff: Unified diff of the change. Always populated, in preview
              mode and after a real write alike, so the caller always
              has a way to see exactly what changed.
    """

    written_path: str = Field(description="Absolute path of the patched file.")
    replaced_line_count: int = Field(description="Number of original lines removed.")
    inserted_line_count: int = Field(description="Number of new lines inserted.")
    total_lines: int = Field(description="Total lines in the file after patching.")
    preview: bool = Field(
        description="True if this was a dry run and no write occurred."
    )
    message: str | None = Field(
        description=(
            "Set when preview=True. Reminds the caller that nothing was written "
            "and that preview must be set to False to confirm the write."
        )
    )
    diff: str = Field(
        description="Unified diff (with line numbers) of the change."
    )
