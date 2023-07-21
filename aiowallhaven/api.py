from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Dict, Union

import aiohttp
import aiohttp.web
from aiohttp_retry import RetryClient
from aiolimiter import AsyncLimiter

from aiowallhaven.types import api_exception_reasons as exception_reasons
from aiowallhaven.types.wallhaven_types import (
    Purity,
    UserCollectionInfo,
    WallpaperInfo,
    PurityFilter,
    WallpaperCollection,
    WallpaperTag,
    UserSettings,
    SearchFilter,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

LOG = logging.getLogger(__name__)
VERSION = "v1"
BASE_API_URL = "https://wallhaven.cc/api"
RATE_LIMIT = AsyncLimiter(12, 60)  # self tested new API limits


class WallHavenAPI(object):
    __slots__ = "api_key"
    r"""
        Base API Class.
        :api_key: 
            an API Key provided by Wallhaven. 
            If you don't have one get yours at https://wallhaven.cc/settings/account.
    """

    def __init__(self, api_key: str):
        self.api_key: str = api_key

    async def _get_method(self, url: str, params: Dict = None) -> Dict:
        if params is None:
            params = {}

        headers = {
            "X-API-key": f"{self.api_key}",
        }

        async with RATE_LIMIT:
            async with RetryClient() as session:
                req_url = f"{BASE_API_URL}/{VERSION}/{url}"
                async with session.get(
                    req_url, headers=headers, params=params
                ) as response:
                    status_code = response.status
                    match status_code:
                        case HTTPStatus.OK:
                            return await response.json()

                        case HTTPStatus.UNAUTHORIZED:
                            raise aiohttp.web.HTTPUnauthorized(
                                reason=exception_reasons.Unauthorized
                            )

                        case HTTPStatus.TOO_MANY_REQUESTS:
                            raise aiohttp.web.HTTPTooManyRequests(
                                reason=exception_reasons.TooManyRequests
                            )

                        case HTTPStatus.NOT_FOUND:
                            raise aiohttp.web.HTTPNotFound(
                                reason=exception_reasons.NotFoundError
                            )

                        case _:  # general error
                            raise aiohttp.web.HTTPException(
                                reason=exception_reasons.GeneralError.format(
                                    session=session, status_code=status_code
                                )
                            )

    async def get_wallpaper(self, wallpaper_id: str) -> WallpaperInfo:
        url = f"w/{wallpaper_id}"
        json_data = await self._get_method(url)
        wallpaper_info = WallpaperInfo.from_json(json_data["data"])
        return wallpaper_info

    async def search(
        self,
        query: str = None,
        page: int = 1,
        search_filter: SearchFilter = SearchFilter(),
    ):
        query_params: dict = search_filter.to_query_params_dict()
        if query:
            query_params["q"] = query
        query_params["page"] = page

        json_search_results = await self._get_method(
            "search"
            if not query_params
            else f"search?{'&'.join('{}={}'.format(*i) for i in query_params.items())}"
        )

        search_results = WallpaperCollection.from_json(json_search_results)
        return search_results

    async def get_tag(self, tag: int):
        tag_info_json = await self._get_method(f"tag/{tag}")
        tag_info = WallpaperTag.from_json(tag_info_json["data"])
        return tag_info

    async def my_settings(self):
        my_settings_json = await self._get_method("settings")
        my_settings = UserSettings.from_json(my_settings_json["data"])
        return my_settings

    async def get_user_uploads(
        self,
        username: str,
        page: int = 1,
        search_filter: SearchFilter = SearchFilter(
            purity=PurityFilter(Purity.sfw, Purity.sketchy)
        ),
    ):
        return await self.search(
            query=f"@{username}", page=page, search_filter=search_filter
        )

    async def get_user_collections_list(
        self,
        username: str = None,
        search_filter: SearchFilter = SearchFilter(),
    ):
        query_url = "collections"
        query_params = search_filter.to_query_params_dict()

        if username:
            query_url += "/" + username

        json_collections = await self._get_method(query_url, params=query_params)
        collections = []
        for collection in json_collections["data"]:
            collections.append(
                UserCollectionInfo(
                    id=collection["id"],
                    label=collection["label"],
                    count=collection["count"],
                    views=collection["views"],
                )
            )
        return collections

    async def get_user_collection(
        self,
        username: str,
        collection_identifier: Union[str, int],
        page=1,
        is_by_id: bool = False,
        search_filter=SearchFilter(),
    ):
        query_url = ""
        query_params = search_filter.to_query_params_dict()
        query_params["page"] = page

        if is_by_id:
            if not isinstance(collection_identifier, int):
                raise ValueError(exception_reasons.ValueErrorId)
            collection_id = collection_identifier
            query_url = "collections"
            query_url += "/" + username
            query_url += "/" + str(collection_id)
        else:
            collection_name = collection_identifier
            all_collections = await self.get_user_collections_list(username)
            for collection in all_collections:
                if collection.label == collection_name:
                    query_url = "collections"
                    query_url += "/" + username
                    query_url += "/" + str(collection.id)
                    break

        # In case of "by name" search
        if not query_url:
            raise aiohttp.web.HTTPNotFound(reason=exception_reasons.NotFoundError)

        wallpaper_collection_json = await self._get_method(
            query_url, params=query_params
        )

        wallpaper_collection = WallpaperCollection.from_json(wallpaper_collection_json)

        return wallpaper_collection
