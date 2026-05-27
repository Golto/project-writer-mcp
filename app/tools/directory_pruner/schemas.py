from typing import Optional

from pydantic import BaseModel, Field


class PruneEmptyDirectoriesRequest(BaseModel):
    """Input schema for the prune_empty_directories tool.

    Walks a directory tree bottom-up and removes every directory that
    contains no files (after its own children have been pruned). Operates
    on the full project root or a specific subdirectory.

    Attributes:
        project_id: Identifier of the registered project.
        relative_path: Subdirectory to prune, relative to the project root.
                       When None, the entire project is pruned from the root.
        include_hidden: When True, hidden directories (names starting with
                        a dot, e.g. .git, .venv) are eligible for pruning.
                        Defaults to False, leaving hidden directories
                        untouched regardless of their contents.
    """

    project_id: str = Field(description="Registered project identifier.")
    relative_path: Optional[str] = Field(
        default=None,
        description=(
            "Subdirectory to prune, relative to the project root. "
            "Defaults to the project root when not provided."
        ),
    )
    include_hidden: bool = Field(
        default=False,
        description=(
            "Include hidden directories (starting with '.') in the prune sweep. "
            "Defaults to False."
        ),
    )


class PruneEmptyDirectoriesResponse(BaseModel):
    """Output schema for the prune_empty_directories tool.

    Attributes:
        root_path: Absolute path of the directory that was pruned.
        removed_directories: Absolute paths of every directory that was deleted,
                             in the order they were removed (deepest first).
        removed_count: Total number of directories removed.
    """

    root_path: str = Field(description="Absolute path of the pruned root directory.")
    removed_directories: list[str] = Field(
        description="Absolute paths of removed directories, deepest first."
    )
    removed_count: int = Field(description="Total number of directories removed.")