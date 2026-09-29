from dataclasses import dataclass


BINARY_PROBE_BYTES = 8192
"""A file is considered binary if this first chunk contains a null byte."""


class BinaryFileError(ValueError):
    """Raised when a file that looks binary is opened for a text edit."""


class NotUtf8Error(ValueError):
    """Raised when a file is not valid UTF-8 and cannot be edited safely."""


@dataclass
class TextFile:
    """Content of a text file, with line endings normalized for editing.

    Attributes:
        text: Decoded content. When uses_crlf is True, every CRLF has been
              turned into LF, so edits only ever deal with LF.
        uses_crlf: True when every line of the file ends with CRLF. The
                   content is converted back to CRLF when encoded.
    """

    text: str
    uses_crlf: bool


def normalize_newlines(text: str) -> str:
    """Turn CRLF into LF, as models send and expect in edit strings.

    Args:
        text: Any text.

    Returns:
        The same text with every CRLF replaced by LF.
    """
    return text.replace("\r\n", "\n")


def decode_text_file(raw_content: bytes, display_path: str) -> TextFile:
    """Decode a file for editing, refusing content that could be corrupted.

    NOTE: a file whose lines ALL end with CRLF is normalized to LF, then
    restored by encode_text_file, so a Windows file keeps its line endings
    while edit strings written with LF still match. A file mixing both is
    left as is: normalizing it would silently change the lines the caller
    did not touch.

    Args:
        raw_content: Raw bytes of the file.
        display_path: Path relative to the project root, for error messages.

    Returns:
        The decoded text and its line ending convention.

    Raises:
        BinaryFileError: If the file looks binary.
        NotUtf8Error: If the file is not valid UTF-8.
    """
    if b"\x00" in raw_content[:BINARY_PROBE_BYTES]:
        raise BinaryFileError(f"'{display_path}' looks like a binary file and cannot be edited as text.")

    try:
        text = raw_content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise NotUtf8Error(
            f"'{display_path}' is not valid UTF-8 (byte {error.start}), so it cannot be edited "
            f"without risking corruption. Rewrite it entirely with write_project_file if needed."
        ) from error

    crlf_count = text.count("\r\n")
    uses_crlf = crlf_count > 0 and crlf_count == text.count("\n")
    return TextFile(text=normalize_newlines(text) if uses_crlf else text, uses_crlf=uses_crlf)


def encode_text_file(text: str, uses_crlf: bool) -> bytes:
    """Encode edited text back to bytes, restoring the original line endings.

    Args:
        text: Edited text, with LF line endings when uses_crlf is True.
        uses_crlf: Whether the original file used CRLF line endings.

    Returns:
        The UTF-8 bytes to write.
    """
    return (text.replace("\n", "\r\n") if uses_crlf else text).encode("utf-8")


def split_lines(text: str) -> list[str]:
    """Split text into lines on LF only, ignoring the final newline.

    Unlike str.splitlines, a lone CR or a form feed does not start a new
    line, so line numbers match those of editors and of the navigator.

    Args:
        text: Text to split.

    Returns:
        The lines, without their newline characters.
    """
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def line_number_at(text: str, index: int) -> int:
    """Return the 1-indexed line number of a character position.

    Args:
        text: The whole text.
        index: 0-indexed character position in text.

    Returns:
        The line number holding that character.
    """
    return text.count("\n", 0, index) + 1
