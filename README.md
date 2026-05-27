# mcp-project-writer

Write-only MCP server for manipulating files inside registered local projects.
The write-side counterpart to [mcp-project-navigator](https://github.com/Golto/project-navigator-mcp).

Both MCPs share the same project registry (`~/.config/scripts/mcp-project/paths.json`)
so project identifiers are consistent across read and write operations.

## Tools

| Tool | Description |
|---|---|
| `write_project_file` | Write (create or overwrite) a file with full content |
| `patch_project_file` | Replace a line range without touching the rest of the file |
| `delete_file` | Delete a single file |
| `create_directory` | Create a directory and all missing parents |
| `move_file` | Move or rename a file within the project |
| `prune_empty_directories` | Remove all empty directories under a project path (hidden directories excluded by default) |

## Safety

All write operations are path-traversal-safe: the resolved target path is
checked against the registered project root before any filesystem operation.
Paths escaping the project directory raise a `PermissionError`.

## Setup

```toml
# ~/.config/scripts/mcp-project/paths.json
{
  "my-project": "/home/user/projects/my-project"
}
```

Install and run with `uv`:

```bash
uv run main.py
```

## Project registry

Edit `~/.config/scripts/mcp-project/paths.json` directly to add or remove
projects. The file is shared with mcp-project-navigator.