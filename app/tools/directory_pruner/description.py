TOOL_DESCRIPTION = """\
Remove every empty directory below a directory of a registered project.

Directories that only contain empty directories are removed too, in a \
single pass. Useful after moving or deleting files. The starting directory \
itself is never removed; hidden directories are left alone unless \
include_hidden=true, and '.git' is never touched. The reply lists the \
removed directories, relative to the project root.\
"""
