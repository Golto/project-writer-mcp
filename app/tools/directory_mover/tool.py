import os
from pathlib import Path

from app.core import (
    PROTECTED_ENTRY_NAMES,
    ProtectedPathError,
    build_not_found_message,
    pluralize,
    resolve_entry_in_project,
    to_relative_display,
)
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import MoveDirectoryRequest


project_storage = get_project_storage()


def _find_protected_entry(directory: Path) -> Path | None:
    """Look for a protected entry such as '.git' anywhere below a directory.

    Symbolic links are not followed, so a link cannot make the scan leave
    the directory.

    Args:
        directory: Absolute path of the directory to scan.

    Returns:
        The first protected entry found, or None.
    """
    for current_directory, subdirectory_names, file_names in os.walk(directory):
        for name in subdirectory_names + file_names:
            if name.casefold() in PROTECTED_ENTRY_NAMES:
                return Path(current_directory, name)
    return None


def _count_files(directory: Path) -> int:
    """Count the files below a directory, symbolic links included, without following them.

    Args:
        directory: Absolute path of the directory.

    Returns:
        The number of non-directory entries at any depth.
    """
    return sum(len(file_names) for _, _, file_names in os.walk(directory))


def move_directory(request: MoveDirectoryRequest) -> str:
    """Move or rename a directory and its whole content inside a registered project.

    The destination must not exist, so no file is ever overwritten and no
    directory merged. A directory holding a protected entry ('.git' of a
    nested repository or submodule) is refused, like any path through one.

    Args:
        request: Project, source directory, destination and parent policy.

    Returns:
        A one-line summary with both paths and the number of files moved.

    Raises:
        PathOutsideProjectError: If a path escapes the project root, or
                                 designates the project root itself.
        ProtectedPathError: If a path is inside '.git', or the source
                            contains a '.git' entry.
        FileNotFoundError: If the source does not exist, or the destination
                           parent is missing and create_parents is False.
        NotADirectoryError: If the source is a file or a symbolic link.
        FileExistsError: If the destination already exists.
        ValueError: If the destination lies inside the source.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    source = resolve_entry_in_project(project_root, request.source_path)
    destination = resolve_entry_in_project(project_root, request.destination_path)
    source_display = to_relative_display(project_root, source)
    destination_display = to_relative_display(project_root, destination)

    if not (source.exists() or source.is_symlink()):
        raise FileNotFoundError(
            build_not_found_message(project_root, request.source_path, "Source directory", looks_for_directory=True)
        )
    if source.is_symlink() or not source.is_dir():
        raise NotADirectoryError(
            f"'{source_display}' is not a directory. Use move_file to move a file or a symbolic link."
        )

    is_case_only_rename = (
        destination.exists()
        and os.path.samestat(source.lstat(), destination.lstat())
        and str(source).casefold() == str(destination).casefold()
    )
    if (destination.exists() or destination.is_symlink()) and not is_case_only_rename:
        raise FileExistsError(
            f"Destination '{destination_display}' already exists: directories are never merged. "
            f"To move '{source_display}' inside it, use destination_path="
            f"'{Path(destination_display, source.name).as_posix()}'."
        )

    if destination.is_relative_to(source) and not is_case_only_rename:
        raise ValueError(
            f"Cannot move '{source_display}' into its own subdirectory '{destination_display}'."
        )

    protected_entry = _find_protected_entry(source)
    if protected_entry is not None:
        raise ProtectedPathError(
            f"'{source_display}' contains '{to_relative_display(project_root, protected_entry)}' "
            f"(a nested repository or a submodule), which is protected: it cannot be moved "
            f"through this server."
        )

    if request.create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    elif not destination.parent.exists():
        raise FileNotFoundError(
            f"Destination directory '{to_relative_display(project_root, destination.parent)}' "
            f"does not exist. Set create_parents=true to create it automatically."
        )

    file_count = _count_files(source)
    # NOTE: the destination does not exist (or is the source itself for a
    # case-only rename), so rename behaves the same on POSIX and Windows.
    source.rename(destination)

    return f"Moved directory '{source_display}' to '{destination_display}' ({pluralize(file_count, 'file')})."


register_tool(move_directory, MoveDirectoryRequest, TOOL_DESCRIPTION)
