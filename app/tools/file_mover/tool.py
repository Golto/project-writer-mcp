import os
from pathlib import Path

from app.mcp import get_mcp
from app.storage import get_project_storage
from app.core import resolve_entry_in_project

from .schemas import MoveFileRequest, MoveFileResponse

mcp = get_mcp()
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


@mcp.tool()
def move_file(request: MoveFileRequest) -> MoveFileResponse:
    """Move or rename a file inside a registered project.

    Both source and destination must remain within the project root and
    outside '.git'. Raises an error if the source does not exist or if the
    destination already exists and overwrite is False. A symbolic link is
    moved itself, never its target; a relative link may no longer resolve
    once moved. Behaves the same on POSIX and Windows, including case-only
    renames on case-insensitive filesystems.
    """
    project_root = project_storage.resolve_project_path(request.project_id)

    source = resolve_entry_in_project(project_root, request.source_path)
    destination = resolve_entry_in_project(project_root, request.destination_path)

    # NOTE: exists() follows symlinks, so a broken link would look missing.
    source_is_link = source.is_symlink()

    if not (source_is_link or source.exists()):
        raise FileNotFoundError(f"Source file '{source}' does not exist.")

    if source.is_dir() and not source_is_link:
        raise IsADirectoryError(
            f"Source '{source}' is a directory. This tool only moves individual files."
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
            f"Destination '{destination}' already exists. "
            f"Set overwrite=True to replace it."
        )

    if request.create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    elif not destination.parent.exists():
        raise FileNotFoundError(
            f"Destination directory '{destination.parent}' does not exist. "
            f"Set create_parents=True to create it automatically."
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

    return MoveFileResponse(
        source_path=str(source),
        destination_path=str(destination),
        overwritten=will_overwrite,
    )
