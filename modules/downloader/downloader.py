import os
import sys
import logging
from dataclasses import dataclass
from http import HTTPStatus

import asyncio
import aiofiles
import aiohttp
import aiohttp.web

from aiolimiter import AsyncLimiter
from modules.aiowallhaven_api.api import WallHavenAPI

DOWNLOADS_PER_MINUTE = 200
DOWNLOADS_RATE_LIMIT = AsyncLimiter(DOWNLOADS_PER_MINUTE)
LOGGER_FORMAT = "[{levelname}]: {message}"


@dataclass
class CollectionTask:
    """
    Container stores info about a single collection download.
    """
    username: str
    collection_name: str
    urls: list
    save_dir: str


@dataclass
class UploadsTask:
    """
    Container stores info about a single uploads download.
    """
    username: str
    urls: list
    save_dir: str


class WallhavenDownloader:
    def _setup_logger(self, log_level):
        self._logger = logging.getLogger(__name__)
        logger_handler = logging.StreamHandler(sys.stdout)
        logger_formatter = logging.Formatter(fmt=LOGGER_FORMAT, style='{')
        logger_handler.setFormatter(logger_formatter)
        logger_handler.setLevel(log_level)
        self._logger.addHandler(logger_handler)
        self._logger.setLevel(log_level)
        self._logger.propagate = False

    def __init__(self,
                 api_key: str = "",
                 download_directory: str = "Downloads",
                 async_downloads: int = 1,
                 log_level: str = "WARNING"):
        """
        :param api_key:
        User's API key (optional), allows to download private
        collections and NSFW content.

        :param download_directory:
        Defines a directory where wallpapers are stored.

        :param async_downloads:
        Count of parallel (asynchronous) downloads.

        :param log_level:
        Set default python log level (e.g. INFO, WARNING, DEBUG, ERROR, FATAL)
        """

        self._api = WallHavenAPI(api_key)
        self._pending_tasks = []
        self._local_wallpaper_ids = []
        self._download_directory = download_directory
        self._async_downloads = async_downloads

        self._setup_logger(log_level)

        if not api_key:
            self._logger.warning("API key is not set")

        if not os.path.exists(self._download_directory):
            os.mkdir(self._download_directory)
            return

        # Collect all the existing wallpapers ids from download_directory,
        # so we can skip such downloads later
        for subdir, dirs, files in os.walk(download_directory):
            for file in files:
                f_name = os.path.join(subdir, file)
                wallpaper_id = f_name[f_name.rfind('-') + 1: f_name.rfind('.')]
                self._local_wallpaper_ids.append(wallpaper_id)

    async def _is_wallpaper_exist_locally(self, wallpaper_id):
        return wallpaper_id in self._local_wallpaper_ids

    async def _download_wallpaper(self, save_dir, url):
        filename = os.path.basename(url)
        save_path = os.path.join(save_dir, filename)
        wallpaper_id = filename[filename.rfind('-') + 1:filename.rfind('.')]

        if await self._is_wallpaper_exist_locally(wallpaper_id):
            self._logger.info("already exists, skipping...")
            return

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        async with DOWNLOADS_RATE_LIMIT:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    status_code = response.status
                    match status_code:
                        case HTTPStatus.OK:
                            try:
                                async with aiofiles.open(save_path, 'wb') as f:
                                    content = await response.read()
                                    await f.write(content)
                            except Exception:
                                if os.path.exists(save_path):
                                    os.remove(save_path)
                        case HTTPStatus.TOO_MANY_REQUESTS:
                            msg = "requests limit reached!"
                            msg += " please rerun script later"
                            msg += " or check your rate limit/async downloads"
                            self._logger.warning(msg)
                            raise aiohttp.web.HTTPTooManyRequests()
                        case _:
                            raise aiohttp.web.HTTPException()

    async def _append_collection_task(self, username, collection):
        res = await self._api.get_user_collection(username, collection)

        if not res:
            return

        last_page = res['meta']['last_page']
        save_dir = os.path.join(
            self._download_directory, "collections", username, collection)

        new_task = CollectionTask(username, collection, [], save_dir)

        for cur_page in range(1, last_page + 1):
            self._logger.info(f"\tpage: {cur_page}/{last_page}")
            walls = await self._api.get_user_collection(username, collection, cur_page)
            for wall in walls['data']:
                new_task.urls.append(wall['path'])

        self._pending_tasks.append(new_task)

    async def _append_uploads_task(self, username):
        user_uploads = await self._api.search(q=f"@{username}", page="1")
        if not user_uploads:
            return

        save_dir = os.path.join(self._download_directory, "uploads", username)
        last_page = user_uploads['meta']['last_page']
        total = user_uploads['meta']['total']
        if total == 0:
            return

        new_task = UploadsTask(username, [], save_dir)
        for cur_page in range(1, last_page + 1):
            walls = await self._api.search(q=f"@{username}", page=f"{cur_page}")
            for wall in walls['data']:
                new_task.urls.append(wall['path'])

        self._pending_tasks.append(new_task)

    async def perform_tasks(self):
        while self._pending_tasks:
            task = self._pending_tasks.pop()
            collection_name = os.path.basename(task.save_dir)
            self._logger.warning(f"downloading in progress: '{collection_name}'")

            d_tasks = []
            urls_count = len(task.urls)
            current_url = 0

            while task.urls:
                current_url += 1
                url = task.urls.pop()
                progress = f"{(current_url / urls_count) * 100:.2f}"
                self._logger.info(f" [~{progress}%], downloading: {url}")

                cor = self._download_wallpaper(task.save_dir, url)
                d_tasks.append(asyncio.create_task(cor))

                full_queue = len(d_tasks) == self._async_downloads
                latest_downloads = len(task.urls) == 0

                if full_queue or latest_downloads:
                    await asyncio.wait(d_tasks, return_when=asyncio.ALL_COMPLETED)
                    d_tasks.clear()

    async def add_tasks(self, collections, uploads):
        for collection in (collections if collections else []):
            username = collection[0]
            user_collections = collection[1:]
            for user_collection in user_collections:
                self._logger.warning(f"adding collection task: '{user_collection}'")
                await self._append_collection_task(username, user_collection)

        for username in (uploads if uploads else []):
            self._logger.warning(f"adding uploads task: {username}")
            await self._append_uploads_task(username)
