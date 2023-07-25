from typing import Optional, Callable
from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 65536


@dataclass
class DownloadTaskInfo:
    url: str
    save_dir: str
    filename: Optional[str]
    chunk_size: Optional[int] = DEFAULT_CHUNK_SIZE

    start_downloading_callback: Optional[Callable] = None
    chunk_downloaded_callback: Optional[Callable] = None
    finish_callback: Optional[Callable] = None
    fail_callback: Optional[Callable] = None

    _id: Optional[int] = None
    _file_size_bytes: int = None

    def get_id(self):
        return self._id

    def get_filesize(self):
        return self._file_size_bytes
