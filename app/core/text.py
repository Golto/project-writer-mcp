def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Join a count and a noun, choosing the singular or plural form.

    Args:
        count: Number of items.
        singular: Noun used when count is exactly 1.
        plural: Noun used otherwise. Defaults to singular followed by 's'.

    Returns:
        A string such as '1 line' or '3 lines'.
    """
    noun = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {noun}"


def count_lines(content: bytes) -> int:
    """Count the lines of a file content the way an editor displays them.

    A final line without a trailing newline still counts as a line.

    Args:
        content: Raw content of the file.

    Returns:
        The number of lines, 0 for an empty content.
    """
    newline_count = content.count(b"\n")
    has_unterminated_last_line = bool(content) and not content.endswith(b"\n")
    return newline_count + (1 if has_unterminated_last_line else 0)
