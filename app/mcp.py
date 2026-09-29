from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings


_mcp: FastMCP | None = None


# ----------------------------------------------------------------
# Instance lifecycle
# ----------------------------------------------------------------

def init() -> None:
    """Create the shared FastMCP instance.

    Must be called exactly once, before importing any tool module, since
    tools decorate themselves on the instance at import time. The instance
    starts with DNS rebinding protection disabled, which is the safe default
    for stdio. Network transports tighten it afterwards through
    configure_transport_security(), on this same instance.

    Raises:
        RuntimeError: If the instance has already been created. Replacing it
                      would silently drop every tool registered on the
                      previous one.
    """
    global _mcp

    if _mcp is not None:
        raise RuntimeError(
            "FastMCP instance already initialized. Use "
            "configure_transport_security() to change its settings."
        )

    _mcp = FastMCP(
        "ProjectWriter",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        ),
    )


def get_mcp() -> FastMCP:
    """Return the shared FastMCP instance.

    Raises:
        RuntimeError: If init() has not been called yet.
    """
    if _mcp is None:
        raise RuntimeError("FastMCP instance not initialized. Call init() first.")
    return _mcp


# ----------------------------------------------------------------
# Transport security
# ----------------------------------------------------------------

def build_transport_security(allowed_hosts: list[str] | None) -> TransportSecuritySettings:
    """Build DNS rebinding protection settings from a host whitelist.

    Each allowed host is also accepted as an http origin, so that browser
    based clients served from those hosts pass the Origin check.

    Args:
        allowed_hosts: Hosts to whitelist, e.g. ["192.168.1.24:*", "localhost:*"].
                       The ":*" suffix accepts any port. None disables the
                       protection entirely.

    Returns:
        Settings ready to be assigned to the FastMCP instance.
    """
    if allowed_hosts is None:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=[f"http://{host}" for host in allowed_hosts],
    )


def configure_transport_security(allowed_hosts: list[str] | None) -> None:
    """Apply DNS rebinding protection to the existing FastMCP instance.

    Mutates the settings in place instead of recreating the instance, so the
    tools already registered on it are kept. FastMCP reads
    settings.transport_security when it builds the SSE / HTTP app, so this
    must be called before run().

    Args:
        allowed_hosts: Hosts to whitelist, see build_transport_security().
                       None disables the protection.

    Raises:
        RuntimeError: If init() has not been called yet.
    """
    get_mcp().settings.transport_security = build_transport_security(allowed_hosts)
