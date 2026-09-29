from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.limits import MAX_EDITS_PER_CALL


OLD_STRING_DESCRIPTION = (
    "Exact text to replace, copied from the current file: same characters, indentation "
    "and line breaks, but WITHOUT the line-number prefixes ('12 \u2502 ') shown by "
    "read_project_file. Must match exactly one place unless replace_all is true: include "
    "2 or 3 surrounding lines when the text alone is not unique."
)
NEW_STRING_DESCRIPTION = "Text that replaces old_string. An empty string deletes old_string."
REPLACE_ALL_DESCRIPTION = "Replace every occurrence of old_string instead of requiring exactly one."


class TextEditSpec(BaseModel):
    """One exact-text replacement requested by the caller.

    Attributes:
        old_string: Exact text to replace, copied from the file.
        new_string: Replacement text. Empty to delete old_string.
        replace_all: Replace every occurrence instead of requiring exactly one.
    """

    old_string: str = Field(description=OLD_STRING_DESCRIPTION)
    new_string: str = Field(description=NEW_STRING_DESCRIPTION)
    replace_all: bool = Field(default=False, description=REPLACE_ALL_DESCRIPTION)


class EditFileRequest(BaseModel):
    """Input schema for the edit_project_file tool.

    Two equivalent forms are accepted, exactly one per call: old_string and
    new_string (with replace_all) for a single edit, or edits for several.

    NOTE: the single-edit form mirrors the Edit tool of Claude Code, the
    habit models most often fall back on. Refusing it would cost a failed
    call and a retry every time.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Path to the file to edit, relative to the project root.
        old_string: Exact text to replace, for a single edit.
        new_string: Replacement text, for a single edit.
        replace_all: Replace every occurrence, for a single edit.
        edits: Several replacements, applied in order, all of them or none.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    relative_path: str = Field(
        description="Path to the existing file to edit, relative to the project root (e.g. 'app/core/utils.py').",
    )
    old_string: Optional[str] = Field(
        default=None,
        description=f"Single edit: {OLD_STRING_DESCRIPTION} Leave unset when using edits.",
    )
    new_string: Optional[str] = Field(
        default=None,
        description=f"Single edit: {NEW_STRING_DESCRIPTION} Leave unset when using edits.",
    )
    replace_all: bool = Field(default=False, description=f"Single edit: {REPLACE_ALL_DESCRIPTION}")
    edits: Optional[list[TextEditSpec]] = Field(
        default=None,
        min_length=1,
        max_length=MAX_EDITS_PER_CALL,
        description=(
            "Several edits in one call, instead of old_string/new_string. They are applied in "
            "order, each one on the file as modified by the previous ones, and the file is "
            "written only if every edit succeeds. Example: "
            "[{\"old_string\": \"MAX_SIZE = 10\", \"new_string\": \"MAX_SIZE = 20\"}, "
            "{\"old_string\": \"import os\\n\", \"new_string\": \"\"}]."
        ),
    )

    @model_validator(mode="after")
    def _require_exactly_one_form(self) -> "EditFileRequest":
        """Accept either the single-edit fields or edits, never both nor neither."""
        has_single_edit = self.old_string is not None or self.new_string is not None
        if has_single_edit and self.edits is not None:
            raise ValueError(
                "Give either old_string and new_string for a single edit, or edits for "
                "several, not both. Move old_string and new_string into edits."
            )
        if self.edits is None and (self.old_string is None or self.new_string is None):
            raise ValueError(
                "Missing edit: give old_string and new_string for a single edit "
                "(new_string may be an empty string to delete text), or edits for several."
            )
        return self

    def to_edit_specs(self) -> list[TextEditSpec]:
        """Return the requested edits as a list, whichever form was used.

        Returns:
            The edits in order: the single edit wrapped in a list, or edits.
        """
        if self.edits is not None:
            return self.edits
        # NOTE: both fields are set here, the validator guarantees it.
        return [TextEditSpec(old_string=self.old_string, new_string=self.new_string, replace_all=self.replace_all)]
