TOOL_DESCRIPTION = """\
Write the complete content of a file in a registered project.

Creates the file, or replaces its whole content if it already exists. Use it \
to create new files or to rewrite a file entirely: content must be the full \
file, not a fragment. Missing parent directories are created unless \
create_parents=false.

The write is atomic: an interrupted call leaves the previous content intact. \
Paths are relative to the project root; paths outside the project and \
anything inside '.git' are refused. The reply states whether the file was \
created or overwritten and gives its line count before and after, so an \
unexpected overwrite is visible at once.\
"""
