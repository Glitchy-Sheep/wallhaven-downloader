from enum import Enum
from typing import Optional
from dataclasses import dataclass


class TaskStatus(Enum):
    SCHEDULED = 0
    IN_PROGRESS = 1
    FAILED = 2
    COMPLETED = 3


@dataclass
class DownloadFileInfo:
    url: str
    save_dir: str
    filename: str
    chunk_size: int
    status: TaskStatus
    exception: Optional[BaseException] = None


@dataclass
class ProgressbarSettings:
    show_total_progress: bool = True
    show_task_progress: bool = False
    main_pbar_pos: int = 0
