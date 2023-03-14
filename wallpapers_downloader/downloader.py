import os
from dataclasses import dataclass

from wallpapers_downloader.logger import get_downloader_logger
from aiowallhaven.wallhaven_types import Purity, Category


@dataclass
class CollectionTask:
    username: str
    save_directory: str
    collections: list[str]


@dataclass
class UploadTask:
    username: str
    save_directory: str


class WallhavenDownloader:
    @staticmethod
    def _get_local_wallpapers_ids(root_path):
        """
            Collect all the existing wallpapers ids from download_directory,
            so we can skip such wallpapers later
        """
        ids = []
        for subdir, dirs, files in os.walk(root_path):
            for file in files:
                f_name = os.path.join(subdir, file)
                wallpaper_id = f_name[f_name.rfind('-')+1: f_name.rfind('.')]
                ids.append(wallpaper_id)
        return ids

    def __init__(self,
                 downloads_directory: str,
                 tasks: list[CollectionTask | UploadTask],
                 purity_filter: Purity,
                 category_filter: Category):

        self._LOG = get_downloader_logger()
        self._tasks = tasks
        self._purity_filter = purity_filter
        self._category_filter = category_filter
        self._downloads_directory = downloads_directory

    async def _download_wallpaper(self, path, url):
        """Planned for future implementation"""
        pass

    async def run_downloader(self):
        """Planned for future implementation"""
        pass
