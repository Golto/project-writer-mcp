import os
import sys
import logging
from pathlib import Path

TRANSPORTS = ("stdio", "sse")

# --- Initialisation globale pour mcp dev/run ---
# Ces imports déclenchent init() + enregistrement des outils
from app.mcp import init, configure_transport_security
init()

from app.storage import configure_storage


def _resolve_paths_dir() -> Path | None:
    """Resolve a custom paths.json directory from CLI flag or env var.

    Must run before `import app.tools`, since tool modules grab the
    ProjectStorage singleton at their own import time. Flag takes
    precedence over the environment variable.
    """
    for arg in sys.argv[1:]:
        if arg.startswith("--paths-dir="):
            return Path(arg.split("=", 1)[1]).expanduser()

    env_value = os.environ.get("MCP_PROJECT_PATHS_DIR")
    if env_value:
        return Path(env_value).expanduser()

    return None


configure_storage(_resolve_paths_dir())

import app.tools   # noqa: F401
import app.prompts  # noqa: F401
import app.resources  # noqa: F401

from app.mcp import get_mcp
mcp = get_mcp()  # objet global visible par `mcp dev` et `mcp run`
# -----------------------------------------------


def _parse_allowed_hosts(raw_value: str) -> list[str]:
    """Split a comma separated --allowed-hosts value into clean host entries.

    Surrounding whitespace is stripped and empty entries are dropped, so that
    "a:*, b:*," yields ["a:*", "b:*"].

    Args:
        raw_value: The raw flag value, without the "--allowed-hosts=" prefix.

    Returns:
        The list of non-empty host entries.
    """
    return [host.strip() for host in raw_value.split(",") if host.strip()]


def main() -> None:
    transport = "stdio"
    host = "0.0.0.0"
    port = 8003
    allowed_hosts: list[str] | None = None

    for arg in sys.argv[1:]:
        if arg.startswith("--transport="):
            transport = arg.split("=", 1)[1]
        elif arg.startswith("--host="):
            host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])
        elif arg.startswith("--allowed-hosts="):
            allowed_hosts = _parse_allowed_hosts(arg.split("=", 1)[1])

    if transport not in TRANSPORTS:
        logging.warning(
            f"Usage: main.py [--transport={'|'.join(TRANSPORTS)}]"
            " [--host=...] [--port=...] [--allowed-hosts=host1,host2]"
            " [--paths-dir=...]"
        )
        sys.exit(1)

    if transport == "sse":
        # NOTE: on modifie l'instance existante au lieu d'en recréer une,
        # sinon les outils enregistrés à l'import seraient perdus et la
        # protection ne serait jamais appliquée au serveur réellement lancé.
        configure_transport_security(allowed_hosts)
        mcp.settings.host = host
        mcp.settings.port = port

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
