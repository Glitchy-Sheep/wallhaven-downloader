import os
from enum import Enum
from http import HTTPStatus
from dataclasses import dataclass
from functools import partial

import asyncio
from typing import Optional

import aiohttp
import aiofiles
import aiofiles.os

from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm
from aiohttp_retry.client import RetryClient
from aiohttp_retry.retry_options import RetryOptionsBase, ExponentialRetry


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


UNLIMITED_AIOLIMITER = AsyncLimiter(1000000, 1)
DEFAULT_PROGRESSBAR_OPTIONS = ProgressbarSettings(True, True, 0)
DEFAULT_RETRY_OPTIONS = ExponentialRetry(
    # The following values are default and set "by sight" for general purpose
    attempts=4,
    start_timeout=1.0,
    max_timeout=10.0,
    statuses={429, 500, 502, 503, 504}
)


async def default_fail_handler_callback(fail_info: DownloadFileInfo):
    filepath = os.path.join(fail_info.save_dir, fail_info.filename)
    if await aiofiles.os.path.exists(filepath):
        await aiofiles.os.remove(filepath)


class ConcurrentDownloader:
    def __init__(self,
                 concurrent_tasks_limit: int = 1,
                 progressbars_options: ProgressbarSettings = DEFAULT_PROGRESSBAR_OPTIONS,
                 aio_limiter: AsyncLimiter = UNLIMITED_AIOLIMITER,
                 retry_options: RetryOptionsBase = DEFAULT_RETRY_OPTIONS,
                 fail_callback=default_fail_handler_callback):

        # Callbacks
        self.fail_callback = fail_callback

        # Progressbars Settings
        self.show_total_progress = progressbars_options.show_total_progress
        self.show_task_progress = progressbars_options.show_task_progress
        self._main_pbar_pos = progressbars_options.main_pbar_pos

        # Downloading settings
        self._aio_limiter = aio_limiter
        self._retry_options = retry_options
        self.concurrent_tasks_limit = concurrent_tasks_limit

        # Task managing containers
        self.pending_tasks:         list[DownloadFileInfo] = []
        self._running_tasks:        list[DownloadFileInfo] = []
        self.finished_tasks:        list[DownloadFileInfo] = []
        self.failed_tasks:          list[DownloadFileInfo] = []
        self._task_workers:         list[asyncio.Task] = []

    @staticmethod
    def _get_filesize_from_response(response):
        try:
            total_size = int(response.headers.get("content-length"), 0)
        except TypeError:
            # Not every file can have a Content-Length header.
            total_size = None
        return total_size

    @staticmethod
    def _get_response_exception(response: aiohttp.ClientResponse):
        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as ex:
            return ex

    @staticmethod
    async def _write_data_to_file(response, save_path, chunk_size, task_pbar):
        async with aiofiles.open(save_path, 'wb') as f:
            async for data in response.content.iter_chunked(chunk_size):
                await f.write(data)
                task_pbar.update(len(data))

    def _create_task_pbar(self, filesize: int, task_info: DownloadFileInfo, pos=1):
        task_pbar = tqdm(total=filesize,
                         unit='iB',
                         unit_scale=True,
                         desc=task_info.filename,
                         leave=False,
                         position=pos,
                         disable=(not self.show_task_progress))
        return task_pbar

    def _create_general_pbar(self, task_count):
        general_pbar = tqdm(total=task_count,
                            leave=True,
                            position=self._main_pbar_pos,
                            disable=(not self.show_total_progress),
                            colour="green")
        return general_pbar

    async def _download_single_file(self,
                                    task_info: DownloadFileInfo,
                                    pbar_pos=1):
        try:
            save_path = os.path.join(task_info.save_dir, task_info.filename)
            os.makedirs(task_info.save_dir, exist_ok=True)

            async with self._aio_limiter:
                async with RetryClient(retry_options=self._retry_options) as session:
                    response = await session.get(task_info.url)
                    if response.status != HTTPStatus.OK:
                        task_info.exception = self._get_response_exception(response)
                        task_info.status = TaskStatus.FAILED
                        return task_info

                    total_size = self._get_filesize_from_response(response)
                    relative_pbar_pos = self._main_pbar_pos + pbar_pos

                    try:
                        task_pbar = self._create_task_pbar(total_size,
                                                           task_info,
                                                           relative_pbar_pos)

                        await self._write_data_to_file(response,
                                                       save_path,
                                                       task_info.chunk_size,
                                                       task_pbar)
                    finally:
                        task_pbar.clear()
                        task_pbar.close()

                    task_info.status = TaskStatus.COMPLETED
                    return task_info
        except (asyncio.CancelledError, aiohttp.ClientOSError, aiohttp.ClientError) as ex:
            await self.fail_callback(task_info)
            task_info.exception = ex
            task_info.status = TaskStatus.FAILED
            return task_info

    async def _cancel_all_tasks(self):
        for task in self._task_workers:
            task.cancel()
            await task

    def schedule_download(self, url, save_dir, filename=None, chunk_size=1024):
        if filename is None:
            filename = os.path.basename(url)

        self.pending_tasks.append(DownloadFileInfo(
            url=url,
            save_dir=save_dir,
            filename=filename,
            chunk_size=chunk_size,
            status=TaskStatus.SCHEDULED)
        )

    # worker's done callback
    def _mark_task_as_finished(self, _future_placeholder, task_info):
        self._running_tasks.remove(task_info)
        self.finished_tasks.append(task_info)

    def _mark_task_as_running(self, task_info):
        self._running_tasks.append(task_info)

    def _mark_task_as_failed(self, task_info):
        self._running_tasks.remove(task_info)
        self.failed_tasks.append(task_info)

    async def _assign_task_to_worker(self, pbar_pos):
        task_info = self.pending_tasks.pop()
        self._mark_task_as_running(task_info)

        clean_up_callback = partial(self._mark_task_as_finished, task_info=task_info)
        task = asyncio.create_task(
            self._download_single_file(task_info, pbar_pos), name=str(pbar_pos)
        )
        task.add_done_callback(clean_up_callback)

        self._task_workers.append(task)

    async def _assign_initial_tasks(self):
        # assign N tasks to workers, so we will process N tasks simultaneously
        initial_task_count = min(self.concurrent_tasks_limit, len(self.pending_tasks))
        for i in range(initial_task_count):
            relative_pbar_pos = self._main_pbar_pos + i + 1
            await self._assign_task_to_worker(relative_pbar_pos)

    async def replace_done_task_with_pending_task(self, done_task):
        self._task_workers.remove(done_task)
        if self.pending_tasks:
            done_pbar_pos = int(done_task.get_name())
            await self._assign_task_to_worker(done_pbar_pos)

    async def wait_for_tasks(self, tasks, general_pbar):
        done, running_tasks = await asyncio.wait(tasks,
                                                 return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            # if any task is failed - cancel others
            task_info: DownloadFileInfo = task.result()
            if task_info.status != TaskStatus.COMPLETED:
                await self._cancel_all_tasks()
                raise task.result().exception

            general_pbar.update()
            await self.replace_done_task_with_pending_task(task)

    async def run_downloader(self):
        total_task_count = len(self.pending_tasks)
        general_pbar = self._create_general_pbar(total_task_count)

        await self._assign_initial_tasks()

        try:
            while self.pending_tasks or self._running_tasks:
                await self.wait_for_tasks(self._task_workers, general_pbar)
        finally:
            general_pbar.close()
