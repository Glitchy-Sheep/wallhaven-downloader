import asyncio
import os
from collections import deque
from http import HTTPStatus
from typing import Optional, Deque, Callable

import aiofiles
import aiofiles.os
import aiofiles.ospath
import aiohttp
import aiohttp.web
from aiolimiter import AsyncLimiter

from async_downloader.types import DownloadTaskInfo, DownloaderStatus


# todo:
# 1. Add aiohttp_retry
# 2. Add proxy support


class ConcurrentDownloader:
    def __init__(
        self,
        max_concurrent_tasks: Optional[int] = 1,
        requests_limiter: Optional[AsyncLimiter] = None,
        start_task_id: Optional[int] = 1,
    ):
        self.requests_limiter: Optional[AsyncLimiter] = requests_limiter

        self._scheduled_tasks: Deque[DownloadTaskInfo] = deque()
        self._in_progress_tasks: Deque[DownloadTaskInfo] = deque()
        self._finished_tasks: Deque[DownloadTaskInfo] = deque()
        self._failed_tasks: Deque[DownloadTaskInfo] = deque()

        self._max_concurrent_tasks = max_concurrent_tasks

        self._async_jobs: Deque[asyncio.Task] = deque()
        self._start_task_id: int = start_task_id

    @staticmethod
    async def _get_filesize_from_response(response: aiohttp.ClientResponse):
        try:
            return int(response.headers["content-length"])
        except (KeyError, ValueError, TypeError):
            return 0

    async def _download_single_file(self, task: DownloadTaskInfo):
        if self.requests_limiter is not None:
            await self.requests_limiter.acquire()

        async with aiohttp.ClientSession() as session:
            async with session.get(task.url) as response:
                if response.status != HTTPStatus.OK:
                    response.raise_for_status()

                task._file_size_bytes = await self._get_filesize_from_response(response)

                save_path = os.path.join(task.save_dir, task.filename)
                await aiofiles.os.makedirs(os.path.dirname(save_path), exist_ok=True)
                async with aiofiles.open(save_path, "wb") as f:
                    if task.start_downloading_callback is not None:
                        await task.start_downloading_callback(task)
                    async for data in response.content.iter_chunked(task.chunk_size):
                        await f.write(data)
                        if task.chunk_downloaded_callback is not None:
                            await task.chunk_downloaded_callback(task, len(data))

    async def _cleanup_failed_task(self, task: DownloadTaskInfo):
        self._in_progress_tasks.remove(task)
        self._failed_tasks.appendleft(task)

        file_path = os.path.join(task.save_dir, task.filename)
        if await aiofiles.ospath.exists(file_path):
            await aiofiles.os.remove(file_path)

        if task.fail_callback is not None:
            await task.fail_callback(task)

    async def _start_download_worker(self, task: DownloadTaskInfo):
        try:
            await self._download_single_file(task)
            if task.finish_callback is not None:
                await task.finish_callback(task)
            self._in_progress_tasks.remove(task)
            self._finished_tasks.appendleft(task)
        except asyncio.CancelledError:
            # Task can be cancelled on top level,
            # so we just do a cleanup before return
            await self._cleanup_failed_task(task)
        except (aiohttp.ClientError, aiohttp.ClientOSError):
            # But if the task itself has errors
            # then it must propagate them further after cleaning up
            await self._cleanup_failed_task(task)
            raise

    async def _start_task_processing(self, task_id: int):
        task_info = self._scheduled_tasks.popleft()
        task_info._id = task_id
        self._in_progress_tasks.appendleft(task_info)
        self._async_jobs.appendleft(
            asyncio.create_task(
                self._start_download_worker(task_info), name=f"{task_id}"
            )
        )

    async def _replace_finished_job_with_pending(self, job: asyncio.Task):
        job_task_id = int(job.get_name())
        self._async_jobs.remove(job)
        await self._start_task_processing(job_task_id)

    async def _start_initial_tasks(self, start_id: int):
        self._start_task_id = start_id

        tasks_to_perform = min(self._max_concurrent_tasks, len(self._scheduled_tasks))

        for task_id in range(
            self._start_task_id, tasks_to_perform + self._start_task_id
        ):
            await self._start_task_processing(task_id)

    async def append_task(self, task: DownloadTaskInfo):
        self._scheduled_tasks.appendleft(task)

    async def get_status(self):
        return DownloaderStatus(
            scheduled_tasks_count=len(self._scheduled_tasks),
            finished_tasks_count=len(self._finished_tasks),
            failed_tasks_count=len(self._failed_tasks),
            in_progress_tasks_count=len(self._in_progress_tasks),
        )

    async def run_downloader(
        self, start_id=1, tasks_status_changed_callback: Callable = None
    ):
        if len(self._scheduled_tasks) == 0:
            return

        await self._start_initial_tasks(start_id)

        while self._scheduled_tasks or self._in_progress_tasks:
            done, pending = await asyncio.wait(
                self._async_jobs, return_when=asyncio.FIRST_COMPLETED
            )

            for async_job in done:
                if tasks_status_changed_callback is not None:
                    tasks_status_changed_callback(await self.get_status())

                # If any task encounters an error,
                # cancel the remaining tasks
                # and wait for the cancellation process to complete.
                if async_job.exception() is not None:
                    for unfinished_task in pending:
                        unfinished_task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    raise async_job.exception()

                if self._scheduled_tasks:
                    await self._replace_finished_job_with_pending(async_job)
