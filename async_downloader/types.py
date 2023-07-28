from typing import Optional, Callable
from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 65536


@dataclass
class DownloadTaskInfo:
    url: str
    save_dir: str
    filename: Optional[str] = None
    chunk_size: Optional[int] = DEFAULT_CHUNK_SIZE

    start_downloading_callback: Optional[Callable] = None
    chunk_downloaded_callback: Optional[Callable] = None
    finish_callback: Optional[Callable] = None
    fail_callback: Optional[Callable] = None

    headers: Optional[dict] = None

    _id: Optional[int] = None
    _file_size_bytes: int = None

    def get_id(self):
        return self._id

    def get_filesize(self):
        return self._file_size_bytes

    def __post_init__(self):
        if self.filename is None:
            self.filename = self.url.split("/")[-1]


@dataclass()
class DownloaderStatus:
    scheduled_tasks_count: int
    in_progress_tasks_count: int
    finished_tasks_count: int
    failed_tasks_count: int
