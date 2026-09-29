from dataclasses import dataclass

from .edit_diagnostics import explain_missing_match
from .text_file import line_number_at, normalize_newlines


MAX_LISTED_OCCURRENCES = 10
"""An ambiguous old_string lists the lines of its occurrences up to this count."""


class EditError(ValueError):
    """Raised when an edit cannot be applied. Nothing is written in that case."""


@dataclass
class TextEdit:
    """One exact-text replacement.

    Attributes:
        old_string: Exact text to find, with LF line endings.
        new_string: Replacement text, with LF line endings.
        replace_all: Replace every occurrence instead of requiring exactly one.
    """

    old_string: str
    new_string: str
    replace_all: bool = False


@dataclass
class EditResult:
    """Outcome of a successful sequence of edits.

    Attributes:
        text: Content after every edit.
        replacement_count: Total number of replaced occurrences. Larger than
                           the number of edits when replace_all was used.
    """

    text: str
    replacement_count: int


def _occurrence_indexes(text: str, old_string: str) -> list[int]:
    """Find the start index of every non-overlapping occurrence.

    Args:
        text: Text to search.
        old_string: Non-empty text to find.

    Returns:
        The 0-indexed start of each occurrence, in order.
    """
    indexes: list[int] = []
    start = text.find(old_string)
    while start != -1:
        indexes.append(start)
        start = text.find(old_string, start + len(old_string))
    return indexes


def _edit_label(edit_number: int, edit_count: int) -> str:
    """Name an edit in messages, only numbering it when there are several.

    Args:
        edit_number: 1-indexed position of the edit.
        edit_count: Total number of edits in the request.

    Returns:
        'Edit 2 of 3: ' or an empty string for a single edit.
    """
    return f"Edit {edit_number} of {edit_count}: " if edit_count > 1 else ""


def _sequence_hint(edit_number: int) -> str:
    """Remind that edits see the output of the previous ones, from edit 2 on."""
    if edit_number == 1:
        return ""
    return (
        " Edits are applied in order: this one sees the file as already modified "
        "by the previous edits of the same call."
    )


def apply_edits(text: str, edits: list[TextEdit], display_path: str) -> EditResult:
    """Apply exact-text replacements in order, all of them or none.

    Each edit works on the text produced by the previous ones. The first
    edit that cannot be applied raises, and since the input text is never
    mutated, the caller simply does not write anything.

    Args:
        text: Current content of the file, with LF line endings.
        edits: Replacements to apply, in order.
        display_path: Path relative to the project root, for messages.

    Returns:
        The edited text and the number of replaced occurrences.

    Raises:
        EditError: If an old_string is empty, equal to its new_string, not
                   found, or found several times without replace_all. The
                   message says which edit failed, why, and how to fix it.
    """
    edit_count = len(edits)
    replacement_count = 0

    for edit_number, edit in enumerate(edits, start=1):
        label = _edit_label(edit_number, edit_count)
        old_string = normalize_newlines(edit.old_string)
        new_string = normalize_newlines(edit.new_string)

        if not old_string:
            raise EditError(
                f"{label}old_string is empty. To create or fully rewrite a file, use "
                f"write_project_file. To insert text, put a neighbouring line in old_string "
                f"and repeat it in new_string along with the new lines. No change was written."
            )
        if old_string == new_string:
            raise EditError(f"{label}old_string and new_string are identical. No change was written.")

        occurrences = _occurrence_indexes(text, old_string)

        if not occurrences:
            raise EditError(
                f"{label}old_string was not found in '{display_path}'. No change was written.\n"
                f"{explain_missing_match(text, old_string)}{_sequence_hint(edit_number)}"
            )

        if len(occurrences) > 1 and not edit.replace_all:
            line_numbers = [str(line_number_at(text, index)) for index in occurrences]
            listed = ", ".join(line_numbers[:MAX_LISTED_OCCURRENCES])
            if len(line_numbers) > MAX_LISTED_OCCURRENCES:
                listed += ", ..."
            raise EditError(
                f"{label}old_string appears {len(occurrences)} times in '{display_path}' "
                f"(lines {listed}). No change was written. Add surrounding lines to old_string "
                f"so that it matches only one place, or set replace_all=true to replace every "
                f"occurrence."
            )

        text = text.replace(old_string, new_string) if edit.replace_all else (
            text[:occurrences[0]] + new_string + text[occurrences[0] + len(old_string):]
        )
        replacement_count += len(occurrences) if edit.replace_all else 1

    return EditResult(text=text, replacement_count=replacement_count)
