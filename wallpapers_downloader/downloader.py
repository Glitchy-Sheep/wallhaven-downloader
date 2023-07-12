import os

from tqdm.asyncio import tqdm
from aiolimiter import AsyncLimiter

from async_downloader.concurrent_downloader import (
    ConcurrentDownloader,
    ProgressbarSettings,
)
from aiowallhaven.wallhaven_types import Purity, Category
from aiowallhaven.api import WallHavenAPI
from wallpapers_downloader.logger import get_downloader_logger
from wallpapers_downloader.types import CollectionTask, UploadTask

# Be aware that the limits for the w.wallhaven.cc domain may change over time.
DOWNLOADER_AIOLIMITER = AsyncLimiter(1.062, 1)


class WallhavenDownloader:
    @staticmethod
    def _get_local_wallpapers_ids(root_path):
        """
        Collect all the existing wallpapers ids from root_path directory,
        so we can skip such wallpapers later
        """
        ids = []
        for subdir, dirs, files in os.walk(root_path):
            for file in files:
                f_name = os.path.join(subdir, file)
                wallpaper_id = f_name[f_name.rfind("-") + 1 : f_name.rfind(".")]
                ids.append(wallpaper_id)
        return ids

    def __init__(
        self,
        token: str,
        downloads_directory: str,
        tasks: list[CollectionTask | UploadTask],
        workers: int,
        purity_filter: Purity,
        category_filter: Category,
    ):
        self._LOG = get_downloader_logger()
        self._api = WallHavenAPI(api_key=token)
        self._downloads_directory = downloads_directory
        self._tasks = tasks
        self._workers = workers
        self._purity_filter = purity_filter
        self._category_filter = category_filter

        self.concurrent_downloader = ConcurrentDownloader(
            concurrent_tasks_limit=workers,
            aio_limiter=DOWNLOADER_AIOLIMITER,
            progressbars_options=ProgressbarSettings(True, True, 0),
        )

    async def _download_collection(
        self, username: str, collection_name: str, save_path: str
    ):
        local_wallpapers_ids = self._get_local_wallpapers_ids(save_path)
        collection_info = await self._api.get_user_collection(
            username, collection_name, page=1
        )

        total_pages = collection_info["meta"]["last_page"]
        pages_fetch_pbar = tqdm(
            total=total_pages,
            leave=False,
            desc=f"Fetching collection info: {collection_name}",
        )
        for page in range(1, total_pages + 1):
            collection_info = await self._api.get_user_collection(
                username, collection_name, page=page
            )
            for wallpaper in collection_info["data"]:
                # skip wallpaper if we already downloaded it before
                if wallpaper["id"] in local_wallpapers_ids:
                    continue

                self.concurrent_downloader.schedule_download(
                    save_dir=save_path, filename=None, url=wallpaper["path"]
                )
            pages_fetch_pbar.update()

        pages_fetch_pbar.close()
        await self.concurrent_downloader.run_downloader()

    async def _download_collections(self, task: CollectionTask):
        username = task.username
        if len(task.collections) == 0:
            collections = await self._api.get_collections(
                username, purity=self._purity_filter
            )
            for collection in collections["data"]:
                task.collections.append(collection["label"])

        for collection_name in task.collections:
            save_dir = os.path.join(task.save_directory, collection_name)
            await self._download_collection(username, collection_name, save_dir)

    async def _download_uploads(self, task: UploadTask):
        username = task.username
        uploads = await self._api.get_user_uploads(username, self._purity_filter)
        total_pages = uploads["meta"]["last_page"]
        local_wallpapers_ids = self._get_local_wallpapers_ids(task.save_directory)

        page_scan_pbar = tqdm(total=total_pages, leave=False)
        page_scan_pbar.desc = "Getting collection info, please wait..."
        for page in range(1, total_pages + 1):
            uploads = await self._api.get_user_uploads(
                username, self._purity_filter, page=page
            )
            for wallpaper in uploads["data"]:
                if wallpaper["id"] in local_wallpapers_ids:
                    continue
                self.concurrent_downloader.schedule_download(
                    save_dir=task.save_directory, filename=None, url=wallpaper["path"]
                )
            page_scan_pbar.update()

        page_scan_pbar.close()
        await self.concurrent_downloader.run_downloader()

    async def run_downloader(self):
        while len(self._tasks) != 0:
            task = self._tasks.pop()
            if isinstance(task, CollectionTask):
                await self._download_collections(task)
            elif isinstance(task, UploadTask):
                await self._download_uploads(task)
