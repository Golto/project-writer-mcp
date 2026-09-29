import os
import stat
import tempfile
from pathlib import Path


TEMPORARY_SUFFIX = ".tmp"


def _read_default_file_mode() -> int:
    """Compute the permission bits a newly created file normally receives.

    mkstemp creates its file with mode 0o600, which would make every new
    project file private to its owner. New files get 0o666 masked by the
    process umask instead, like open() would give them.

    NOTE: the umask can only be read by setting it. This runs once, at import
    time, while the server is still single-threaded.

    Returns:
        The permission bits for new files, such as 0o644.
    """
    current_umask = os.umask(0)
    os.umask(current_umask)
    return 0o666 & ~current_umask


DEFAULT_FILE_MODE = _read_default_file_mode()


def write_bytes_atomically(target: Path, content: bytes) -> None:
    """Replace the content of target so that readers see the old or the new file, never a mix.

    The content is written to a temporary file in the same directory,
    flushed to disk, then moved over target with os.replace, which is atomic
    on both POSIX and Windows when source and destination share a filesystem.
    An interruption (crash, full disk, killed server) therefore leaves target
    untouched instead of truncated.

    The permission bits of an existing target are carried over to the new
    file. A hard link to the old file keeps the old content, since target
    becomes a new file.

    Args:
        target: Absolute path of the file to write. Its parent must exist and
                target must not be a directory.
        content: Complete new content of the file.

    Raises:
        OSError: If the temporary file cannot be written or moved. The
                 temporary file is removed and target is left unchanged.
    """
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=TEMPORARY_SUFFIX,
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        file_mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else DEFAULT_FILE_MODE
        os.chmod(temporary_path, file_mode)
        os.replace(temporary_path, target)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
