from pathlib import Path


PROTECTED_ENTRY_NAMES = frozenset({".git"})
"""Entries that no tool may create, modify, move or delete, at any depth.

NOTE: '.git' holds executable hooks ('.git/hooks/pre-commit') and the whole
history. Writing there would let a caller run code on the next git command,
so it is refused outright rather than left to convention. It also covers the
'.git' FILE of worktrees and submodules, which redirects git elsewhere.
Names are compared case-insensitively, since '.GIT' is the same directory on
Windows and macOS default filesystems.
"""


class PathOutsideProjectError(PermissionError):
    """Raised when a user-supplied path is absolute or resolves outside the project root."""


class ProtectedPathError(PermissionError):
    """Raised when a path designates or crosses a protected entry such as '.git'."""


def assert_within_project(project_root: Path, target: Path, requested_path: str | Path) -> None:
    """Raise an error if target is outside the project root.

    Prevents path-traversal attacks where a relative_path like
    '../../etc/passwd' would escape the registered project directory.
    The message only quotes the path given by the caller, never the
    absolute location of the project on disk.

    Args:
        project_root: Absolute, resolved path to the project root.
        target: Absolute, resolved path to the file or directory to validate.
        requested_path: Path as given by the caller, quoted in the message.

    Raises:
        PathOutsideProjectError: If target is not contained within project_root.
    """
    if not target.is_relative_to(project_root):
        raise PathOutsideProjectError(
            f"Path '{requested_path}' resolves outside the project root. "
            f"Only files inside the project can be modified."
        )


def assert_not_protected(project_root: Path, target: Path) -> None:
    """Raise an error if target is, or lies inside, a protected entry.

    Every component of the path relative to the project root is checked, so
    both '.git' itself and anything below it are refused.

    Args:
        project_root: Absolute, resolved path to the project root.
        target: Absolute path inside project_root, already confined.

    Raises:
        ProtectedPathError: If any component of the path is a protected name.
    """
    relative_target = target.relative_to(project_root)
    for part in relative_target.parts:
        if part.casefold() in PROTECTED_ENTRY_NAMES:
            location = "is" if part == relative_target.name else f"is inside '{part}', which is"
            raise ProtectedPathError(
                f"'{relative_target.as_posix()}' {location} protected: "
                f"git internals cannot be modified through this server."
            )


def resolve_path_in_project(project_root: Path, relative_path: str | Path) -> Path:
    """Resolve a path whose CONTENT is accessed, confined to the project.

    Used by the tools that write a file or create a directory. The path is
    fully resolved, so writing through an internal symbolic link updates its
    target; that target must still be inside the project and outside any
    protected entry.

    Args:
        project_root: Absolute, resolved path to the project root.
        relative_path: Path supplied by the caller, relative to project_root.

    Returns:
        The absolute, fully resolved path.

    Raises:
        PathOutsideProjectError: If relative_path is absolute or resolves
                                 outside project_root.
        ProtectedPathError: If the resolved path is inside a protected entry.
    """
    candidate = Path(relative_path)

    if candidate.is_absolute():
        raise PathOutsideProjectError(
            f"Absolute paths are not allowed: '{relative_path}'. "
            f"Use a path relative to the project root, such as 'src/main.py'."
        )

    target = (project_root / candidate).resolve()
    assert_within_project(project_root, target, relative_path)
    assert_not_protected(project_root, target)
    return target


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
    on file CONTENT (write, patch) use resolve_path_in_project instead, so
    writing through an internal link still updates its target.

    Args:
        project_root: Absolute, resolved path to the project root.
        relative_path: Path supplied by the caller, relative to project_root.

    Returns:
        The absolute path of the entry, with its parent resolved and its
        final component left untouched.

    Raises:
        PathOutsideProjectError: If relative_path is absolute, does not
                                 designate a named entry ('.', '..', 'dir/..'),
                                 or its parent resolves outside project_root.
        ProtectedPathError: If the entry is or lies inside a protected entry.
    """
    candidate = Path(relative_path)

    if candidate.is_absolute():
        raise PathOutsideProjectError(
            f"Absolute paths are not allowed: '{relative_path}'. "
            f"Use a path relative to the project root, such as 'src/main.py'."
        )

    if candidate.name in ("", ".", ".."):
        raise PathOutsideProjectError(
            f"Path '{relative_path}' does not designate a named file or directory inside the project."
        )

    parent = (project_root / candidate.parent).resolve()
    assert_within_project(project_root, parent, relative_path)

    entry = parent / candidate.name
    assert_not_protected(project_root, entry)
    return entry


def to_relative_display(project_root: Path, path: Path) -> str:
    """Express a path inside the project as the caller should see it.

    Every message and tool output goes through this helper, so the absolute
    location of the project on disk never reaches the caller.

    Args:
        project_root: Absolute, resolved path to the project root.
        path: Absolute path inside project_root.

    Returns:
        A POSIX path relative to the project root, '.' for the root itself.
    """
    return path.relative_to(project_root).as_posix()
