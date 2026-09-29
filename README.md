# mcp-project-writer

Write-only MCP server for manipulating files inside registered local projects.
The write-side counterpart to [mcp-project-navigator](https://github.com/Golto/project-navigator-mcp).

Both MCPs share the same project registry (`~/.config/scripts/mcp-project/paths.json`)
so project identifiers are consistent across read and write operations.

## Tools

| Tool | Description |
|---|---|
| `edit_project_file` | Replace exact text in an existing file, without rewriting it |
| `write_project_file` | Write (create or overwrite) a file with its full content |
| `delete_file` | Delete a single file |
| `move_file` | Move or rename a single file within the project |
| `move_directory` | Move or rename a whole directory within the project |
| `create_directory` | Create a directory and all missing parents |
| `prune_empty_directories` | Remove all empty directories under a project path (hidden directories excluded by default) |

## Editing files

`edit_project_file` locates the text to change by its exact content, never by
line numbers: line numbers go stale after the first change, which made the
former line-range patcher corrupt files. Content stays valid whatever was
edited before.

- A single edit is given as `old_string` / `new_string` (optionally
  `replace_all`); several edits as `edits=[{...}, ...]`, applied in order,
  each on the result of the previous ones.
- All or nothing: the file is written only if every edit succeeds, and the
  write is atomic.
- `old_string` must match exactly one place, unless `replace_all` is set; an
  ambiguous match lists the lines of every occurrence.
- On success, the reply is a numbered diff with the NEW line numbers of the
  file, so no extra read is needed to know where things are.
- On failure, nothing is written and the error diagnoses the usual mistakes:
  line-number prefixes copied from the navigator output, an indentation or
  whitespace mismatch (the exact text of the file is quoted), or a typo or
  outdated text (the closest block of the file is quoted with its line
  numbers and similarity).
- CRLF files keep their line endings, and the presence or absence of a final
  newline is preserved. Binary and non-UTF-8 files are refused.

## Designed for language models

The tools follow the same conventions as mcp-project-navigator:

- Parameters are flat. Each tool is written against a Pydantic request model
  and registered through `register_tool` (`app/tools/registration.py`), which
  derives a flat signature from it.
- Replies are short text, not JSON, with paths relative to the project root.
  `write_project_file` reports whether the file was created or overwritten,
  with its line count before and after.
- Error messages only quote relative paths and suggest a fix: similar
  existing files or directories when a path is missing, the parameter to set
  otherwise.
- The description read by the model lives in each tool's `description.py`.
  Docstrings stay written for developers.

## Safety

- All paths are confined to the registered project root: absolute paths and
  paths resolving outside the project raise `PathOutsideProjectError`.
- `.git` is protected at any depth, case-insensitively, including through
  symbolic links and the `.git` file of worktrees and submodules: no tool can
  write, edit, create, move, delete or prune inside it (`ProtectedPathError`).
  A directory containing a `.git` entry cannot be moved either.
- Files are written atomically (temporary file, fsync, `os.replace`): an
  interrupted write never leaves a truncated file, and permission bits are
  preserved.
- Operations on entries (delete, move) act on symbolic links themselves,
  never on their targets, like `rm` and `mv`.
- Directories are never merged: `move_directory` requires a destination that
  does not exist yet.

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
