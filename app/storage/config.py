import json
import logging
import sys
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def _default_config_folder() -> Path:
    """Return the platform-appropriate configuration directory.

    On Windows, configuration is stored under %APPDATA%\\mcp-project-writer.
    On all other platforms, the XDG-style ~/.config/scripts/mcp-project
    is used -- the same directory as mcp-project-navigator so both MCPs
    share the same project registry.

    Returns:
        An absolute Path to the configuration directory.
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming"
        return base / "mcp-project-navigator"
    return Path.home() / ".config" / "scripts" / "mcp-project"


class StorageConfig:
    """Manages the on-disk configuration layout for the MCP project writer.

    Reads the same paths.json registry used by mcp-project-navigator so
    that project identifiers are consistent across both MCPs.

    Attributes:
        base_path: Root directory of the configuration.
        paths_file: Path to the JSON file that stores project paths.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """Initialise the configuration.

        Args:
            base_path: Override the default configuration directory.
                       When None, the platform-appropriate default is used.
        """
        self.base_path = Path(base_path) if base_path is not None else _default_config_folder()
        self.paths_file = self.base_path / "paths.json"
        self._ensure_structure()

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _ensure_structure(self) -> None:
        """Create the configuration directory and seed missing files."""
        self.base_path.mkdir(parents=True, exist_ok=True)

        if not self.paths_file.exists():
            self.paths_file.write_text("{}", encoding="utf-8")
            logger.debug("Created empty paths file at %s", self.paths_file)

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def load_paths(self) -> dict[str, str]:
        """Load the project-id-to-path mapping from disk.

        Returns:
            A dictionary mapping each project identifier to its absolute
            path string. Returns an empty dict if the file is missing or
            malformed.
        """
        if not self.paths_file.exists():
            return {}

        try:
            with self.paths_file.open(encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            if not isinstance(data, dict):
                logger.warning(
                    "Paths file %s does not contain a JSON object; ignoring.",
                    self.paths_file,
                )
                return {}

            return data

        except json.JSONDecodeError as exc:
            logger.error(
                "Paths file %s is malformed and could not be parsed: %s",
                self.paths_file,
                exc,
            )
            return {}
        except OSError as exc:
            logger.error("Could not read paths file %s: %s", self.paths_file, exc)
            return {}