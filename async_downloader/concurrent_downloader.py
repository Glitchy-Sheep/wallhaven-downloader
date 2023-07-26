import asyncio
import os
from typing import List

import aiofiles
import aiofiles.os
import aiofiles.ospath
import aiohttp
from aiolimiter import AsyncLimiter

from async_downloader.types import DownloadTaskInfo


# todo:
# 1. Add aiohttp_retry
# 2. Add proxy support
# 3. Add error statuses handler


class ConcurrentDownloader:
    def __init__(
        self,
        max_concurrent_tasks: int = 1,
        requests_limiter: AsyncLimiter = None,
        start_task_id: int = 1,
    ):
        self.scheduled_tasks: List[DownloadTaskInfo] = []
        self.in_progress_tasks: List[DownloadTaskInfo] = []
        self.finished_tasks: List[DownloadTaskInfo] = []
        self.failed_tasks: List[DownloadTaskInfo] = []

        self.max_concurrent_tasks = max_concurrent_tasks
        self.requests_limiter = requests_limiter

        self._async_jobs: list[asyncio.Task] = []
        self._start_task_id = start_task_id

    @staticmethod
    async def _get_filesize_from_response(response):
        try:
            return int(response.headers["content-length"])
        except (KeyError, ValueError, TypeError):
            return 0

    @staticmethod
    async def _download_single_file(self, task: DownloadTaskInfo):
        if self.requests_limiter is not None:
            await self.requests_limiter.acquire()

        async with aiohttp.ClientSession() as session:
            async with session.get(task.url) as response:
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

    async def _start_download_worker(self, task: DownloadTaskInfo):
        try:
            await self._download_single_file(self, task)
            if task.finish_callback is not None:
                await task.finish_callback(task)
            self.in_progress_tasks.remove(task)
            self.finished_tasks.append(task)
        except (
            asyncio.CancelledError,
            aiohttp.ClientError,
            aiohttp.ClientOSError,
        ):
            if task.fail_callback is not None:
                await task.fail_callback(task)
            file_path = os.path.join(task.save_dir, task.filename)
            if await aiofiles.ospath.exists(file_path):
                await aiofiles.os.remove(file_path)
            self.in_progress_tasks.remove(task)
            self.failed_tasks.append(task)
            raise

    async def _assign_new_task_to_worker(self, task_id: int):
        task_info = self.scheduled_tasks.pop(0)
        task_info._id = task_id
        self.in_progress_tasks.append(task_info)
        self._async_jobs.append(
            asyncio.create_task(
                self._start_download_worker(task_info), name=f"{task_id}"
            )
        )

    async def _replace_finished_job_with_pending(self, job: asyncio.Task):
        job_task_id = int(job.get_name())
        self._async_jobs.remove(job)
        await self._assign_new_task_to_worker(job_task_id)

    async def append_task(self, task: DownloadTaskInfo):
        self.scheduled_tasks.append(task)

    async def run_downloader(self):
        if len(self.scheduled_tasks) == 0:
            return

        tasks_to_perform = min(self.max_concurrent_tasks, len(self.scheduled_tasks))

        for task_id in range(
            self._start_task_id, tasks_to_perform + self._start_task_id
        ):
            await self._assign_new_task_to_worker(task_id)

        while self.scheduled_tasks or self.in_progress_tasks:
            done, pending = await asyncio.wait(
                self._async_jobs, return_when=asyncio.FIRST_COMPLETED
            )

            for async_job in done:
                if async_job.exception() is not None:
                    for unfinished_task in pending:
                        unfinished_task.cancel()
                    raise async_job.exception()

                if self.scheduled_tasks:
                    await self._replace_finished_job_with_pending(async_job)
