import os

import aiohttp.web
from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm

from aiowallhaven.api import WallHavenAPI
from aiowallhaven.types.wallhaven_types import SearchFilter
from async_downloader.concurrent_downloader import (
    ConcurrentDownloader,
    ProgressbarSettings,
)
from wallpapers_downloader.logger import get_downloader_logger
from wallpapers_downloader.types import CollectionTask, UploadTask, UserCollections

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
        api_key: str,
        downloads_directory: str,
        tasks: list[CollectionTask | UploadTask],
        workers_count: int,
        downloads_filters: SearchFilter = SearchFilter(),
    ):
        self._LOG = get_downloader_logger()
        self._api = WallHavenAPI(api_key=api_key)
        self._downloads_directory = downloads_directory
        self._tasks = tasks
        self._workers = workers_count
        self.search_filter = downloads_filters

        self.concurrent_downloader = ConcurrentDownloader(
            concurrent_tasks_limit=workers_count,
            aio_limiter=DOWNLOADER_AIOLIMITER,
            progressbars_options=ProgressbarSettings(True, True, 0),
        )

    async def _download_collection(
        self, username: str, collection_name: str, save_path: str
    ):
        local_wallpapers_ids = self._get_local_wallpapers_ids(save_path)
        collection_info = await self._api.get_user_collection(
            username, collection_name, search_filter=self.search_filter
        )

        total_pages = collection_info.meta.last_page
        pages_fetch_pbar = tqdm(
            total=total_pages,
            leave=False,
            desc=f"Fetching collection info: {collection_name}",
        )

        print(local_wallpapers_ids)
        for page in range(1, total_pages + 1):
            collection_info = await self._api.get_user_collection(
                username, collection_name, page=page, search_filter=self.search_filter
            )
            for wallpaper in collection_info.wallpapers:
                # skip wallpaper if we already downloaded it before
                if wallpaper.id in local_wallpapers_ids:
                    print(f"Skipping wallpaper: {wallpaper.id}")
                    continue

                self.concurrent_downloader.schedule_download(
                    save_dir=save_path, filename=None, url=wallpaper.path
                )
            pages_fetch_pbar.update()

        pages_fetch_pbar.close()
        await self.concurrent_downloader.run_downloader()

    async def _download_collections(self, task: CollectionTask):
        username = task.username
        if len(task.collections) == 0:
            collections = await self._api.get_user_collections_list(username)
            for collection in collections:
                task.collections.append(collection.label)

        for collection_name in task.collections:
            save_dir = os.path.join(task.save_directory, collection_name)
            await self._download_collection(username, collection_name, save_dir)

    async def _download_uploads(self, task: UploadTask):
        username = task.username
        uploads = await self._api.get_user_uploads(
            username, search_filter=self.search_filter
        )
        total_pages = uploads.meta.last_page
        local_wallpapers_ids = self._get_local_wallpapers_ids(task.save_directory)

        page_scan_pbar = tqdm(total=total_pages, leave=False)
        page_scan_pbar.desc = "Getting collection info, please wait..."
        for page in range(1, total_pages + 1):
            uploads = await self._api.get_user_uploads(
                username, page=page, search_filter=self.search_filter
            )
            for wallpaper in uploads.wallpapers:
                if wallpaper.id in local_wallpapers_ids:
                    continue
                self.concurrent_downloader.schedule_download(
                    save_dir=task.save_directory, url=wallpaper.path
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

    async def retrieve_users_info(self, usernames_list: list) -> list[UserCollections]:
        users_info: list[UserCollections] = []
        retrieve_pbar = tqdm(
            total=len(usernames_list),
            leave=False,
            desc="Retrieving users info...",
            position=0,
        )
        for username in usernames_list:
            try:
                users_info.append(
                    UserCollections(
                        username=username,
                        collections=await self._api.get_user_collections_list(username),
                    )
                )
            except aiohttp.web.HTTPNotFound:
                tqdm.write(f"User {username} not found")
                continue
            finally:
                retrieve_pbar.update()

        retrieve_pbar.close()
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
