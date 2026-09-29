from .atomic_write import write_bytes_atomically
from .diff import format_numbered_diff
from .editing import EditError, EditResult, TextEdit, apply_edits
from .safety import (
    PROTECTED_ENTRY_NAMES,
    PathOutsideProjectError,
    ProtectedPathError,
    assert_not_protected,
    assert_within_project,
    resolve_entry_in_project,
    resolve_path_in_project,
    to_relative_display,
)
from .suggestions import build_not_found_message
from .text import count_lines, pluralize
from .text_file import (
    BinaryFileError,
    NotUtf8Error,
    TextFile,
    decode_text_file,
    encode_text_file,
)

__all__ = [
    "PROTECTED_ENTRY_NAMES",
    "BinaryFileError",
    "EditError",
    "EditResult",
    "NotUtf8Error",
    "PathOutsideProjectError",
    "ProtectedPathError",
    "TextEdit",
    "TextFile",
    "apply_edits",
    "assert_not_protected",
    "assert_within_project",
    "build_not_found_message",
    "count_lines",
    "decode_text_file",
    "encode_text_file",
    "format_numbered_diff",
    "pluralize",
    "resolve_entry_in_project",
    "resolve_path_in_project",
    "to_relative_display",
    "write_bytes_atomically",
]
