from pydantic import BaseModel, Field


class MoveDirectoryRequest(BaseModel):
    """Input schema for the move_directory tool.

    Attributes:
        project_id: Identifier of the registered project.
        source_path: Current path of the directory, relative to the project root.
        destination_path: New path of the directory, relative to the project
                          root. It must not exist: directories are never merged.
        create_parents: When True, missing parent directories of the
                        destination are created automatically. Defaults to True.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    source_path: str = Field(
        description="Current path of the directory to move, relative to the project root (e.g. 'app/utils').",
    )
    destination_path: str = Field(
        description=(
            "New path of the directory, relative to the project root, which must not exist yet "
            "(e.g. 'app/helpers' to rename it, 'lib/utils' to move it into 'lib')."
        ),
    )
    create_parents: bool = Field(
        default=True,
        description="Create missing parent directories of the destination.",
    )
