from mcp.server.fastmcp import FastMCP

_mcp = FastMCP("ProjectWriter")


def get_mcp() -> FastMCP:
    """Get the FastMCP instance."""
    return _mcp