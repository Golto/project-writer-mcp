from pathlib import Path


def assert_within_project(project_root: Path, target: Path) -> None:
    """Raise an error if target is outside the project root.

    Prevents path-traversal attacks where a relative_path like
    '../../etc/passwd' would escape the registered project directory.

    Args:
        project_root: Absolute, resolved path to the project root.
        target: Absolute, resolved path to the file or directory to validate.

    Raises:
        PermissionError: If target is not contained within project_root.
    """
    try:
        target.relative_to(project_root)
    except ValueError:
        raise PermissionError(
            f"Path '{target}' is outside the registered project root '{project_root}'. "
            f"Write operations are restricted to the project directory."
        )


def resolve_entry_in_project(project_root: Path, relative_path: str | Path) -> Path:
    """Resolve a path to the directory ENTRY itself, without following a final symlink.

    Operations that act on an entry rather than on its content (delete,
    move, rename) must not resolve the last path component: if it is a
    symbolic link, Path.resolve() would return the link TARGET, and the
    operation would silently hit another file than the one requested.

    Only the parent directory is resolved, which is enough to confine the
    entry: a single path component appended to a directory inside the
    project always designates an entry inside the project.

    NOTE: this mirrors how rm and mv treat symbolic links. Tools that act
    on file CONTENT (write, patch) keep using a full resolve, so writing
    through an internal link still updates its target.

    Args:
        project_root: Absolute, resolved path to the project root.
        relative_path: Path supplied by the caller, relative to project_root.

    Returns:
        The absolute path of the entry, with its parent resolved and its
        final component left untouched.

    Raises:
        PermissionError: If relative_path is absolute, does not designate
                         a named entry ('.', '..', 'dir/..'), or its parent
                         resolves outside project_root.
    """
    candidate = Path(relative_path)

    if candidate.is_absolute():
        raise PermissionError(
            f"Absolute paths are not allowed: '{relative_path}'. "
            f"Use a path relative to the project root, such as 'src/main.py'."
        )

    if candidate.name in ("", ".", ".."):
        raise PermissionError(
            f"Path '{relative_path}' does not designate a named file inside the project."
        )

    parent = (project_root / candidate.parent).resolve()
    assert_within_project(project_root, parent)

    return parent / candidate.name
