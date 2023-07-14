from dataclasses import dataclass
from aiowallhaven.wallhaven_types import CollectionInfo


@dataclass
class UserCollections:
    """
    Object representing user collections.
    """

    username: str
    collections: list[CollectionInfo]


@dataclass
class CollectionTask:
    """
    Object representing collection task.
    """

    username: str
    save_directory: str
    collections: list[str]


@dataclass
class UploadTask:
    """
    Object representing upload task.
    """

    username: str
    save_directory: str
