from aiolimiter import AsyncLimiter
from async_downloader.types import ProgressbarSettings
from aiohttp_retry import ExponentialRetry

UNLIMITED_AIOLIMITER = AsyncLimiter(1000000, 1)

DEFAULT_PROGRESSBAR_OPTIONS = ProgressbarSettings(
    show_total_progress=True, show_task_progress=True, main_pbar_pos=0
)

DEFAULT_RETRY_OPTIONS = ExponentialRetry(
    # The following values are default and set "by sight" for general purpose
    attempts=4,
    start_timeout=1.0,
    max_timeout=10.0,
    statuses={429, 500, 502, 503, 504},
)
