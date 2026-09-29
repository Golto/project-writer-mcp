TOOL_DESCRIPTION = """\
Move or rename a single file inside a registered project.

destination_path is the full new path of the file, file name included: \
moving 'a.py' into 'lib/' means destination_path='lib/a.py'. Missing \
destination directories are created unless create_parents=false. An \
existing destination file is only replaced with overwrite=true. A symbolic \
link is moved itself, never its target.

If the source does not exist, the error suggests similar existing paths. \
Paths outside the project and anything inside '.git' are refused.\
"""
