from pathlib import Path


def collect_empty_directories(root: Path, include_hidden: bool) -> list[Path]:
    """Collect all empty directories under root in bottom-up order.

    Walks the tree bottom-up so that a directory emptied by the removal of
    its own children is also collected in the same pass. The root itself is
    never included -- only its descendants.

    When include_hidden is False, any directory whose name starts with '.'
    is excluded along with its entire subtree -- the walk does not descend
    into it at all. This protects .git, .venv, and similar directories.

    Args:
        root: Absolute path to the directory to inspect.
        include_hidden: When False, hidden directories (names starting with
                        '.') and all their contents are skipped entirely.

    Returns:
        A list of Path objects for empty directories, ordered deepest-first
        so that callers can safely delete them in iteration order.
    """
    candidates: list[Path] = []
    _collect_recursive(root, root, include_hidden, candidates)
    return candidates


def _collect_recursive(
    root: Path,
    current_directory: Path,
    include_hidden: bool,
    candidates: list[Path],
) -> bool:
    """Recursively collect empty directories, returning True if current is empty.

    Processes children before the parent (bottom-up) so that a directory
    emptied by pruning its children is itself eligible in the same pass.

    Args:
        root: Original sweep root, never added to candidates.
        current_directory: Directory being evaluated in this call.
        include_hidden: When False, hidden directories are skipped entirely.
        candidates: Accumulator list, mutated in place.

    Returns:
        True if current_directory is empty (or became empty after pruning
        its children), False otherwise.
    """
    has_surviving_child = False

    for child in sorted(current_directory.iterdir()):
        if child.is_symlink():
            # Symlinks count as surviving content regardless of target.
            has_surviving_child = True
            continue

        if child.is_dir():
            if not include_hidden and child.name.startswith("."):
                # Hidden subtree: do not descend, treat as surviving content.
                has_surviving_child = True
                continue

            child_is_empty = _collect_recursive(root, child, include_hidden, candidates)
            if not child_is_empty:
                has_surviving_child = True
        else:
            # Regular file: directory is not empty.
            has_surviving_child = True

    is_empty = not has_surviving_child

    if is_empty and current_directory != root:
        candidates.append(current_directory)

    return is_empty