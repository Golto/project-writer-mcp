import os
from pathlib import Path

from app.core import build_not_found_message, resolve_entry_in_project, to_relative_display
from app.storage import get_project_storage
from app.tools.registration import register_tool

from .description import TOOL_DESCRIPTION
from .schemas import MoveFileRequest


project_storage = get_project_storage()


def _is_same_entry(first: Path, second: Path) -> bool:
    """Tell whether two paths designate the very same directory entry.

    True for a case-only rename on a case-insensitive filesystem ('util.py'
    to 'Util.py' on Windows or macOS), where the destination 'exists' only
    because it is the source itself, and for two hard links to one file.
    Symbolic links are not followed.

    Args:
        first: Absolute path of the first entry, which must exist.
        second: Absolute path of the second entry, which must exist.

    Returns:
        True if both paths lead to the same filesystem entry.
    """
    return os.path.samestat(first.lstat(), second.lstat())


def move_file(request: MoveFileRequest) -> str:
    """Move or rename a file inside a registered project.

    Both source and destination must remain within the project root and
    outside '.git'. Raises an error if the source does not exist or if the
    destination already exists and overwrite is False. A symbolic link is
    moved itself, never its target; a relative link may no longer resolve
    once moved. Behaves the same on POSIX and Windows, including case-only
    renames on case-insensitive filesystems.

    Args:
        request: Project, source, destination and overwrite policy.

    Returns:
        A one-line summary of the move, saying whether a file was replaced.

    Raises:
        PathOutsideProjectError: If a path escapes the project root.
        ProtectedPathError: If a path is inside '.git'.
        FileNotFoundError: If the source does not exist (the message
                           suggests similar paths), or the destination
                           directory is missing and create_parents is False.
        IsADirectoryError: If the source or the destination is a directory.
        FileExistsError: If the destination exists and overwrite is False.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    source = resolve_entry_in_project(project_root, request.source_path)
    destination = resolve_entry_in_project(project_root, request.destination_path)
    source_display = to_relative_display(project_root, source)
    destination_display = to_relative_display(project_root, destination)

    # NOTE: exists() follows symlinks, so a broken link would look missing.
    source_is_link = source.is_symlink()

    if not (source_is_link or source.exists()):
        raise FileNotFoundError(build_not_found_message(project_root, request.source_path, "Source file"))

    if source.is_dir() and not source_is_link:
        raise IsADirectoryError(
            f"Source '{source_display}' is a directory: this tool only moves individual files."
        )

    destination_is_occupied = destination.is_symlink() or destination.exists()
    is_same_entry = destination_is_occupied and _is_same_entry(source, destination)
    # NOTE: on a case-insensitive filesystem, 'util.py' to 'Util.py' finds the
    # destination occupied by the source itself: that is a rename, not an
    # overwrite. The same entry under a different name is a hard link.
    is_case_only_rename = is_same_entry and str(source).casefold() == str(destination).casefold()
    will_overwrite = destination_is_occupied and not is_case_only_rename

    if will_overwrite and destination.is_dir() and not destination.is_symlink():
        raise IsADirectoryError(
            f"Destination '{request.destination_path}' is an existing directory. "
            f"Give the full path of the moved file, such as "
            f"'{Path(request.destination_path, source.name).as_posix()}'."
        )

    if will_overwrite and not request.overwrite:
        raise FileExistsError(
            f"Destination '{destination_display}' already exists. "
            f"Set overwrite=true to replace it."
        )

    if request.create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    elif not destination.parent.exists():
        raise FileNotFoundError(
            f"Destination directory '{to_relative_display(project_root, destination.parent)}' "
            f"does not exist. Set create_parents=true to create it automatically."
        )

    if is_same_entry and not is_case_only_rename:
        # NOTE: source and destination are hard links to one file. rename()
        # is then a no-op on POSIX and would leave the source in place, so
        # the source link is removed instead: the destination already holds
        # the very same content.
        source.unlink()
    else:
        # NOTE: Path.rename refuses an existing destination on Windows but
        # silently replaces it on POSIX. Path.replace overwrites on every
        # platform; the overwrite policy has been enforced just above.
        source.replace(destination)

    if will_overwrite:
        return f"Moved '{source_display}' to '{destination_display}', replacing the previous file."
    return f"Moved '{source_display}' to '{destination_display}'."


register_tool(move_file, MoveFileRequest, TOOL_DESCRIPTION)
