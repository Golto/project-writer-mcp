import difflib
import os
from pathlib import Path, PurePosixPath


MAX_SUGGESTIONS = 3
"""Maximum number of alternative paths proposed in a not-found error."""

MAX_SCANNED_FILES = 20_000
"""Stop collecting candidates after this many files, to bound latency."""

NAME_SIMILARITY_CUTOFF = 0.75
"""Minimum difflib ratio between file names for a path to be suggested."""

PATH_SIMILARITY_CUTOFF = 0.9
"""Minimum difflib ratio between full paths for a path to be suggested.

NOTE: much stricter than NAME_SIMILARITY_CUTOFF on purpose: files of the same
directory share a long common prefix, which inflates the ratio of full paths.
'app/core/walkr.py' is 0.8 away from the unrelated 'app/core/search.py',
while real typos in a file or directory name stay above 0.97. Same values as
in mcp-project-navigator.
"""

SKIPPED_DIRECTORY_NAMES = frozenset({"__pycache__", "node_modules"})
"""Generated directories never worth suggesting files from.

NOTE: this server has no .gitignore support, unlike mcp-project-navigator.
Hidden directories ('.venv', '.git') are skipped too, which covers the rest
of the usual noise.
"""


def _list_candidate_paths(
    project_root: Path,
    opened_hidden_directories: frozenset[str],
    includes_hidden_files: bool,
    lists_directories: bool,
) -> list[str]:
    """Collect the relative paths of the project entries that could be suggested.

    Args:
        project_root: Absolute path to the project root.
        opened_hidden_directories: Names of the hidden directories that may be
                                   explored. Every other hidden directory is
                                   skipped with its whole subtree.
        includes_hidden_files: Whether hidden files are candidates.
        lists_directories: Collect directories instead of files.

    Returns:
        POSIX paths relative to the project root, at most MAX_SCANNED_FILES.
    """
    candidates: list[str] = []

    for directory, subdirectory_names, file_names in os.walk(project_root):
        # NOTE: pruning subdirectory_names in place stops os.walk descending.
        subdirectory_names[:] = sorted(
            name for name in subdirectory_names
            if name not in SKIPPED_DIRECTORY_NAMES
            and (not name.startswith(".") or name in opened_hidden_directories)
        )
        relative_directory = Path(directory).relative_to(project_root)
        if lists_directories:
            candidates.extend((relative_directory / name).as_posix() for name in subdirectory_names)
            if len(candidates) >= MAX_SCANNED_FILES:
                return candidates
            continue
        for file_name in sorted(file_names):
            if file_name.startswith(".") and not includes_hidden_files:
                continue
            candidates.append((relative_directory / file_name).as_posix())
            if len(candidates) >= MAX_SCANNED_FILES:
                return candidates

    return candidates


def suggest_similar_paths(
    project_root: Path,
    requested_path: str | Path,
    looks_for_directory: bool = False,
) -> list[str]:
    """Propose existing project files or directories that the caller most likely meant.

    Three strategies are combined, in this order of priority: files carrying
    the exact same name in another directory (a wrong folder), files whose
    name is close to the requested one (a typo in the name), then paths close
    to the requested one as a whole (a typo in a directory name).

    Args:
        project_root: Absolute path to the project root.
        requested_path: Path given by the caller that does not exist.
        looks_for_directory: Suggest directories instead of files.

    Returns:
        Up to MAX_SUGGESTIONS relative paths, best candidates first. Empty
        when nothing is close enough.
    """
    requested = PurePosixPath(Path(requested_path).as_posix())
    # NOTE: only the hidden directories named in the requested path are
    # opened: looking inside '.private' must not drag '.venv' into the
    # results, whose thousands of files would crowd out the real match.
    opened_hidden_directories = frozenset(
        part for part in requested.parent.parts
        if part.startswith(".") and part not in (".", "..")
    )
    candidates = _list_candidate_paths(
        project_root,
        opened_hidden_directories=opened_hidden_directories,
        includes_hidden_files=requested.name.startswith("."),
        lists_directories=looks_for_directory,
    )

    paths_by_name: dict[str, list[str]] = {}
    for candidate in candidates:
        paths_by_name.setdefault(PurePosixPath(candidate).name, []).append(candidate)

    same_name_paths = paths_by_name.get(requested.name, [])
    close_names = difflib.get_close_matches(
        requested.name,
        list(paths_by_name),
        n=MAX_SUGGESTIONS,
        cutoff=NAME_SIMILARITY_CUTOFF,
    )
    close_name_paths = [path for name in close_names for path in paths_by_name[name]]
    close_paths = difflib.get_close_matches(
        str(requested),
        candidates,
        n=MAX_SUGGESTIONS,
        cutoff=PATH_SIMILARITY_CUTOFF,
    )

    unique_suggestions = dict.fromkeys(same_name_paths + close_name_paths + close_paths)
    return list(unique_suggestions)[:MAX_SUGGESTIONS]


def build_not_found_message(
    project_root: Path,
    requested_path: str | Path,
    subject: str = "File",
    looks_for_directory: bool = False,
) -> str:
    """Build a not-found message that helps the caller recover in one step.

    Args:
        project_root: Absolute path to the project root.
        requested_path: Path given by the caller that does not exist.
        subject: What was looked for, capitalized ('File', 'Source directory').
        looks_for_directory: Suggest directories instead of files.

    Returns:
        A message naming the missing path, followed by suggestions when some
        were found.
    """
    message = f"{subject} not found: '{requested_path}'."
    suggestions = suggest_similar_paths(project_root, requested_path, looks_for_directory)

    if suggestions:
        formatted = ", ".join(f"'{suggestion}'" for suggestion in suggestions)
        return f"{message} Did you mean: {formatted}?"
    return message
