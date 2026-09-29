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
                        a dot, e.g. .venv) are eligible for pruning.
                        Defaults to False, leaving hidden directories
                        untouched regardless of their contents. '.git' is
                        never pruned.
    """

    project_id: str = Field(description="Registered project identifier, as returned by list_projects.")
    relative_path: Optional[str] = Field(
        default=None,
        description=(
            "Subdirectory to prune, relative to the project root. "
            "Defaults to the whole project. This directory itself is never removed."
        ),
    )
    include_hidden: bool = Field(
        default=False,
        description="Also prune inside hidden directories (names starting with '.'). '.git' is never pruned.",
    )
