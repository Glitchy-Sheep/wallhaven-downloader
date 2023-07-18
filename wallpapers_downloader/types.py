from dataclasses import dataclass
from aiowallhaven.types.wallhaven_types import UserCollectionInfo


@dataclass
class UserCollections:
    """
    Object representing user collections.
    """

    username: str
    collections: list[UserCollectionInfo]


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
