TOOL_DESCRIPTION = """\
Create a directory, and all its missing parents, in a registered project.

Behaves like 'mkdir -p'. Rarely needed before writing a file, since \
write_project_file creates missing parent directories itself: use it for \
directories meant to stay empty for now. Paths outside the project and \
anything inside '.git' are refused.\
"""
