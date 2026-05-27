from .project import ProjectStorage

_project_storage = ProjectStorage()


def get_project_storage() -> ProjectStorage:
    """Get the shared ProjectStorage instance."""
    return _project_storage