import os

import aiohttp.web
from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm_asyncio

from aiowallhaven.api import WallHavenAPI
from aiowallhaven.types.wallhaven_types import SearchFilter
from async_downloader.concurrent_downloader import ConcurrentDownloader
from async_downloader.types import DownloadTaskInfo, DownloaderStatus
from wallpapers_downloader.types import CollectionTask, UploadTask, UserCollections

COLLECTIONS_PBAR_POS = 0
COLLECTION_PBAR_POS = 1
UPLOADS_PBAR_POS = 1

TASKS_COLOR = "cyan"
GENERAL_PROGRESS_COLOR = "green"
RETRIEVAL_PROGRESS_COLOR = "yellow"

global_task_progress_bars = dict()


async def _create_task_pbar(task_info: DownloadTaskInfo):
    global_task_progress_bars[task_info.get_id()] = tqdm_asyncio(
        desc=task_info.filename,
        total=task_info.get_filesize(),
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        leave=False,
        position=task_info.get_id(),
        colour=TASKS_COLOR,
    )


async def _update_task_pbar(task_info: DownloadTaskInfo, chunks_downloaded: int):
    global_task_progress_bars[task_info.get_id()].update(chunks_downloaded)


async def _close_task_pbar(task_info: DownloadTaskInfo):
    global_task_progress_bars[task_info.get_id()].close()


class WallhavenDownloader:
    def __init__(
        self,
        api_key: str,
        downloads_directory: str,
        tasks_list: list[CollectionTask | UploadTask],
        max_concurrent_downloads: int,
        downloads_filters: SearchFilter = SearchFilter(),
        requests_limiter: AsyncLimiter = None,
    ):
        self._api: WallHavenAPI = WallHavenAPI(api_key=api_key)
        self._downloads_directory: str = downloads_directory
        self._tasks: list[CollectionTask | UploadTask] = tasks_list
        self._max_concurrent_downloads: int = max_concurrent_downloads
        self.search_filter = downloads_filters

        self._concurrent_downloader = ConcurrentDownloader(
            max_concurrent_tasks=max_concurrent_downloads,
            requests_limiter=requests_limiter,
        )

    @staticmethod
    def _get_local_wallpapers_ids(root_path):
        """
        Collect all the existing wallpapers ids from root_path directory,
        so we can skip such wallpapers later

        The file names for wallpapers should match the name on the website.
        For example: wallhaven-ab1c2d.jpg
        """
        ids = []
        for subdir, dirs, files in os.walk(root_path):
            for file in files:
                f_name = os.path.join(subdir, file)
                # extract wallhaven-######.jpg from file name
                wallpaper_id = f_name[f_name.rfind("-") + 1 : f_name.rfind(".")]
                ids.append(wallpaper_id)
        return ids

    async def _download_collection(self, username, collection_name, save_directory):
        collection_save_directory = os.path.join(save_directory, collection_name)
        collection_info = await self._api.get_user_collection(username, collection_name)
        local_wallpapers_ids = self._get_local_wallpapers_ids(collection_save_directory)

        with tqdm_asyncio(
            total=collection_info.meta.last_page,
            desc=f"Retrieving {collection_name} wallpapers...",
            position=COLLECTION_PBAR_POS,
            leave=False,
        ) as collection_pbar:
            for page in range(1, collection_info.meta.last_page + 1):
                wallpapers = (
                    await self._api.get_user_collection(
                        username, collection_name, page=page
                    )
                ).wallpapers
                for wallpaper in wallpapers:
                    if wallpaper.id in local_wallpapers_ids:
                        collection_pbar.write(
                            f"Skipping {wallpaper.id} (already downloaded)"
                        )
                        continue
                    await self._concurrent_downloader.append_task(
                        task=DownloadTaskInfo(
                            url=wallpaper.path,
                            save_dir=collection_save_directory,
                            start_downloading_callback=_create_task_pbar,
                            chunk_downloaded_callback=_update_task_pbar,
                            finish_callback=_close_task_pbar,
                        )
                    )
                collection_pbar.update(1)

        general_tasks_progress_pos = COLLECTION_PBAR_POS + 1
        with tqdm_asyncio(
            desc="Downloading wallpapers",
            total=(
                await self._concurrent_downloader.get_status()
            ).scheduled_tasks_count,
            leave=True,
            position=general_tasks_progress_pos,
            colour=GENERAL_PROGRESS_COLOR,
        ) as general_pbar:
            await self._concurrent_downloader.run_downloader(
                start_id=general_tasks_progress_pos + 1,
                tasks_status_changed_callback=lambda x: general_pbar.update(1),
            )

    async def _download_collections(self, task: CollectionTask):
        if len(task.collections) == 0:
            collections = await self._api.get_user_collections_list(task.username)
            for collection in collections:
                task.collections.append(collection.label)

        with tqdm_asyncio(
            total=len(task.collections),
            desc=f"Downloading {task.username} collections...",
            colour=RETRIEVAL_PROGRESS_COLOR,
        ) as collections_pbar:
            save_directory = os.path.join(
                self._downloads_directory, "collections", task.username
            )
            for collection_name in task.collections:
                await self._download_collection(
                    task.username, collection_name, save_directory
                )
                collections_pbar.update(1)

    async def _download_uploads(self, task: UploadTask):
        uploads_save_directory = os.path.join(
            self._downloads_directory, "uploads", task.username
        )
        uploads_info = await self._api.get_user_uploads(
            username=task.username, search_filter=self.search_filter
        )
        local_wallpapers_ids = self._get_local_wallpapers_ids(uploads_save_directory)

        with tqdm_asyncio(
            total=uploads_info.meta.last_page,
            desc=f"Retrieving {task.username} uploads...",
            position=UPLOADS_PBAR_POS,
            leave=False,
            colour=RETRIEVAL_PROGRESS_COLOR,
        ) as uploads_pbar:
            for page in range(1, uploads_info.meta.last_page + 1):
                uploads_info = await self._api.get_user_uploads(
                    username=task.username, page=page, search_filter=self.search_filter
                )
                for wallpaper in uploads_info.wallpapers:
                    if wallpaper.id in local_wallpapers_ids:
                        uploads_pbar.write(
                            f"Skipping {wallpaper.id} (already downloaded)"
                        )
                        continue

                    await self._concurrent_downloader.append_task(
                        task=DownloadTaskInfo(
                            url=wallpaper.path,
                            save_dir=uploads_save_directory,
                            start_downloading_callback=_create_task_pbar,
                            chunk_downloaded_callback=_update_task_pbar,
                            finish_callback=_close_task_pbar,
                            fail_callback=_close_task_pbar,
                        )
                    )
                uploads_pbar.update(1)

        general_tasks_progress_pos = UPLOADS_PBAR_POS + 1
        with tqdm_asyncio(
            desc="Downloading wallpapers",
            total=(
                await self._concurrent_downloader.get_status()
            ).scheduled_tasks_count,
            leave=True,
            position=general_tasks_progress_pos,
            colour=GENERAL_PROGRESS_COLOR,
        ) as general_pbar:
            await self._concurrent_downloader.run_downloader(
                start_id=general_tasks_progress_pos + 1,
                tasks_status_changed_callback=lambda x: general_pbar.update(1),
            )

    async def run_downloader(self) -> DownloaderStatus:
        while len(self._tasks) != 0:
            task = self._tasks.pop()
            if isinstance(task, CollectionTask):
                await self._download_collections(task)
            elif isinstance(task, UploadTask):
                await self._download_uploads(task)
        return await self._concurrent_downloader.get_status()

    async def retrieve_users_info(self, usernames_list: list) -> list[UserCollections]:
        users_info: list[UserCollections] = []
        for username in usernames_list:
            try:
                users_info.append(
                    UserCollections(
                        username=username,
                        collections=await self._api.get_user_collections_list(username),
                    )
                )
            except aiohttp.web.HTTPNotFound:
                continue

        return users_info

    async def print_users_info(self, usernames_list: list):
        # Sort users_info by collections count,
        # so first user with the most collections will be printed
        users_info = await self.retrieve_users_info(usernames_list)
        users_info = sorted(users_info, key=lambda x: len(x.collections), reverse=True)
        table_width = 20

        for user_info in users_info:
            if not user_info.collections:
                print("-" * table_width * 2)
                print(f"{user_info.username} has no public collections.")
                continue

            header = (
                ("-" * table_width) + f" {user_info.username} " + ("-" * table_width)
            )
            print("=" * len(header))
            print(header)
            print("=" * len(header))
            for collection in user_info.collections or []:
                print(collection)
