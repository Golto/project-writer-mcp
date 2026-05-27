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