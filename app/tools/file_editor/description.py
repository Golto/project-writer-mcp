TOOL_DESCRIPTION = """\
Edit an existing text file of a registered project by replacing exact text, \
without rewriting the whole file.

Prefer it to write_project_file for any change to an existing file: it is \
cheaper, and it cannot alter the lines you did not target. Each edit \
replaces old_string with new_string.

- old_string must be copied exactly from the current file, indentation, \
spaces and line breaks included, but WITHOUT the line-number prefixes \
('12 \u2502 ') that read_project_file adds.
- old_string must match exactly one place. When it is not unique, include 2 \
or 3 surrounding lines, or set replace_all=true to change every occurrence.
- To delete text, use an empty new_string. To insert text, put a \
neighbouring line in old_string and repeat it in new_string together with \
the new lines.

For a single edit, give old_string and new_string directly. For several \
edits in one call, give edits=[{"old_string": ..., "new_string": ...}, ...] \
instead: they are applied in order, each on the result of the previous \
ones, and the file is written only if all of them succeed.

On success, the reply shows a numbered diff of the changes with the NEW line \
numbers of the file. On failure nothing is written, and the error explains \
why: line-number prefixes left in old_string, a whitespace or indentation \
mismatch, or the closest text actually present in the file, quoted with its \
line numbers so it can be copied exactly. Line endings (LF or CRLF) and the \
final newline are preserved. Only UTF-8 text files can be edited; paths \
outside the project and anything inside '.git' are refused.\
"""
