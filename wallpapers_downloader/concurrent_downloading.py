import os
from dataclasses import dataclass
from functools import partial
from contextlib import suppress

import asyncio
import aiohttp
import aiofiles
import aiofiles.os

from tqdm.asyncio import tqdm


@dataclass
class DownloadFileInfo:
    url: str
    filename: str
    save_dir: str
    chunk_size: int


async def default_fail_handler_callback(fail_info: DownloadFileInfo):
    filepath = os.path.join(fail_info.save_dir, fail_info.filename)
    if await aiofiles.os.path.exists(filepath):
        with suppress(FileNotFoundError):
            await aiofiles.os.remove(filepath)


class ConcurrentDownloader:
    def __init__(self,
                 concurrent_tasks_limit=1,
                 show_total_progress=True,
                 show_task_progress=False,
                 main_pbar_pos=0,
                 fail_callback=default_fail_handler_callback):
        # callbacks
        self.fail_callback = fail_callback

        # Settings
        self.concurrent_tasks_limit = concurrent_tasks_limit
        self.show_total_progress = show_total_progress
        self.show_task_progress = show_task_progress
        self._general_pbar_pos = main_pbar_pos

        # Task managing containers
        self.pending_tasks:        list[DownloadFileInfo] = []
        self._in_progress_tasks:    list[DownloadFileInfo] = []
        self.finished_tasks:       list[DownloadFileInfo] = []
        self._task_workers:         list[asyncio.Task] = []
        self.failed_tasks:          list[DownloadFileInfo] = []

        # File managing containers (very important because of file locks)
        # clean up method will clean it up if something fails (and also delete trash)
        self.opened_files_fds = []

    @staticmethod
    def _get_filesize_from_response(response):
        try:
            total_size = int(response.headers.get("content-length"), 0)
        except TypeError:
            # Not every file can have a Content-Length header.
            total_size = None
        return total_size

    def _create_task_pbar(self, size: int, task_info: DownloadFileInfo, pos=1):
        task_pbar = tqdm(total=size,
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
                            position=self._general_pbar_pos,
                            disable=(not self.show_total_progress))
        return general_pbar

    async def _write_data_to_file(self, response, save_path, chunk_size, task_pbar):
        async with aiofiles.open(save_path, 'wb') as f:
            self.opened_files_fds.append(f.fileno())
            async for data in response.content.iter_chunked(chunk_size):
                await f.write(data)
                task_pbar.update(len(data))
            self.opened_files_fds.remove(f.fileno())

    async def _download_single_file(self,
                                    task_info: DownloadFileInfo,
                                    pbar_pos=1):
        save_path = os.path.join(task_info.save_dir, task_info.filename)
        os.makedirs(task_info.save_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(task_info.url) as response:
                total_size = self._get_filesize_from_response(response)
                relative_pbar_pos = self._general_pbar_pos + pbar_pos + 1
                task_pbar = self._create_task_pbar(total_size, task_info,
                                                   relative_pbar_pos)

                try:
                    chunk_size = task_info.chunk_size
                    await self._write_data_to_file(response,
                                                   save_path,
                                                   chunk_size,
                                                   task_pbar)
                except (OSError, aiohttp.ClientResponseError):
                    await self.fail_callback(task_info)

                task_pbar.close()

    async def _failure_cleanup(self):
        for fd in self.opened_files_fds:
            os.close(fd)

        for unfinished_task in self._in_progress_tasks:
            path = os.path.join(unfinished_task.save_dir, unfinished_task.filename)
            if await aiofiles.os.path.exists(path):
                with suppress(FileNotFoundError):
                    await aiofiles.os.remove(path)

            self.failed_tasks.append(unfinished_task)

    def schedule_download(self, save_dir, filename, url, chunk_size=1024):
        if filename is None:
            filename = os.path.basename(url)

        new_task = DownloadFileInfo(url=url,
                                    filename=filename,
                                    save_dir=save_dir,
                                    chunk_size=chunk_size)

        self.pending_tasks.append(new_task)

    def _move_task_from_running_to_finished(self, _future_pholder, task_info):
        self._in_progress_tasks.remove(task_info)
        self.finished_tasks.append(task_info)

    async def _assign_task_to_worker(self, pbar_pos):
        task_info = self.pending_tasks.pop()
        self._in_progress_tasks.append(task_info)
        task = asyncio.create_task(
            self._download_single_file(task_info, pbar_pos), name=str(pbar_pos)
        )
        clean_up_callback = partial(self._move_task_from_running_to_finished, task_info=task_info)
        task.add_done_callback(clean_up_callback)
        self._task_workers.append(task)

    async def run_downloader(self):
        total_task_count = len(self.pending_tasks)
        general_pbar = self._create_general_pbar(total_task_count)

        # assign N tasks to workers, so we will process N tasks simultaneously
        for i in range(min(self.concurrent_tasks_limit, len(self.pending_tasks))):
            await self._assign_task_to_worker(i)

        # if any task is finished - replace it with a new one from pending
        while self.pending_tasks or self._in_progress_tasks:
            try:
                done, pending = await asyncio.wait(self._task_workers,
                                                   return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    general_pbar.update()
                    self._task_workers.remove(task)
                    if self.pending_tasks:
                        left_pbar_pos = int(task.get_name())
                        await self._assign_task_to_worker(left_pbar_pos)
            except (asyncio.CancelledError, KeyboardInterrupt):
                await self._failure_cleanup()
                break

        general_pbar.close()
