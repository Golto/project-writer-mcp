TOOL_DESCRIPTION = """\
Move or rename a whole directory, with everything it contains, inside a \
registered project.

destination_path is the full new path of the directory and must not exist \
yet: directories are never merged. To move 'app/utils' into 'lib', use \
destination_path='lib/utils'; to rename it, use 'app/helpers'. Missing \
parent directories are created unless create_parents=false.

Use move_file for a single file. A directory containing a '.git' entry (a \
nested repository or a submodule) cannot be moved, nor can the project root \
itself; paths outside the project and anything inside '.git' are refused. \
Moving code does not update its imports: search for the old path afterwards \
with search_project_content.\
"""
