TOOL_DESCRIPTION = """\
Delete a single file of a registered project.

Only files can be deleted: a directory is refused, and directories left \
empty afterwards can be removed with prune_empty_directories. A symbolic \
link is deleted itself, never its target. If the file does not exist, the \
error suggests similar existing paths; set allow_missing=true to make the \
deletion idempotent instead. Paths outside the project and anything inside \
'.git' are refused.\
"""
