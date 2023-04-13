from dataclasses import dataclass

@dataclass
class CollectionTask:
    username: str
    save_directory: str
    collections: list[str]


@dataclass
class UploadTask:
    username: str
    save_directory: str
