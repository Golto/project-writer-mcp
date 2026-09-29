# mcp-project-writer

Write-only MCP server for manipulating files inside registered local projects.
The write-side counterpart to [mcp-project-navigator](https://github.com/Golto/project-navigator-mcp).

Both MCPs share the same project registry (`~/.config/scripts/mcp-project/paths.json`)
so project identifiers are consistent across read and write operations.

## Tools

| Tool | Description |
|---|---|
| `write_project_file` | Write (create or overwrite) a file with its full content |
| `delete_file` | Delete a single file |
| `create_directory` | Create a directory and all missing parents |
| `move_file` | Move or rename a file within the project |
| `prune_empty_directories` | Remove all empty directories under a project path (hidden directories excluded by default) |

## Designed for language models

The tools follow the same conventions as mcp-project-navigator:

- Parameters are flat. Each tool is written against a Pydantic request model
  and registered through `register_tool` (`app/tools/registration.py`), which
  derives a flat signature from it.
- Replies are one short sentence, not JSON, with paths relative to the
  project root. `write_project_file` reports whether the file was created or
  overwritten, with its line count before and after.
- Error messages only quote relative paths and suggest a fix: similar
  existing paths when a file is missing, the parameter to set otherwise.
- The description read by the model lives in each tool's `description.py`.
  Docstrings stay written for developers.

## Safety

- All paths are confined to the registered project root: absolute paths and
  paths resolving outside the project raise `PathOutsideProjectError`.
- `.git` is protected at any depth, case-insensitively, including through
  symbolic links and the `.git` file of worktrees and submodules: no tool can
  write, create, move, delete or prune inside it (`ProtectedPathError`).
- Files are written atomically (temporary file, fsync, `os.replace`): an
  interrupted write never leaves a truncated file, and permission bits are
  preserved.
- Operations on entries (delete, move) act on symbolic links themselves,
  never on their targets, like `rm` and `mv`.

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
