from pydantic import BaseModel, Field


class MoveFileRequest(BaseModel):
    """Input schema for the move_file tool.

    Moves or renames a file within a registered project. Both the source
    and destination must remain within the same project root.

    Attributes:
        project_id: Identifier of the registered project.
        source_path: Current path of the file, relative to the project root.
        destination_path: Target path, relative to the project root.
                          The file will be renamed if only the filename
                          changes, or relocated if the directory changes.
        create_parents: When True, missing intermediate directories in the
                        destination path are created automatically.
                        Defaults to True.
        overwrite: When True, an existing file at destination_path is
                   replaced. When False, a FileExistsError is raised if
                   the destination already exists. Defaults to False.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    source_path: str = Field(
        description="Current path of the file, relative to the project root.",
    )
    destination_path: str = Field(
        description=(
            "New path of the file, relative to the project root, including its "
            "file name (e.g. 'app/utils/helpers.py', not 'app/utils')."
        ),
    )
    create_parents: bool = Field(
        default=True,
        description="Create missing intermediate directories at the destination.",
    )
    overwrite: bool = Field(
        default=False,
        description="Replace the destination file if it already exists.",
    )
