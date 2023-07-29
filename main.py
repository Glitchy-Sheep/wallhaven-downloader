import asyncio
import http
import os
import time

import aiohttp.web
from dotenv import load_dotenv

import arguments_parser.parser as arg_parser
from aiowallhaven.types.wallhaven_types import SearchFilter
from wallpapers_downloader.downloader import WallhavenDownloader
from aiolimiter import AsyncLimiter

# Try to get api key from cmd first then from env, but cmd has major priority
WALLHAVEN_API_KEY = arg_parser.get_api_key()

if not WALLHAVEN_API_KEY:
    load_dotenv("settings.env")
    WALLHAVEN_API_KEY = os.getenv("WALLHAVEN_API_KEY")

if not WALLHAVEN_API_KEY:
    WALLHAVEN_API_KEY = ""
    print(
        """
    WARNING: No api key provided
    Some private functionality will be unavailable
    Please provide your API key either by api_key argument
    or in settings.env file (WALLHAVEN_API_KEY = your_api_key).
    """
    )


async def amain(event_loop):
    search_filter = SearchFilter(
        category=arg_parser.get_category_filter(),
        purity=arg_parser.get_purity_filter(),
    )

    downloader = WallhavenDownloader(
        api_key=WALLHAVEN_API_KEY,
        downloads_directory=arg_parser.get_downloads_path(),
        tasks_list=arg_parser.get_all_tasks(),
        max_concurrent_downloads=arg_parser.get_workers_count(),
        downloads_filters=search_filter,
        requests_limiter=AsyncLimiter(arg_parser.get_requests_per_second(), 1),
    )

    if arg_parser.get_info_usernames():
        await downloader.print_users_info(arg_parser.get_info_usernames())
    else:
        start_time = time.time()
        status = await downloader.run_downloader()
        end_time = time.time()
        total_time_min = (end_time - start_time) / 60

        print(
            f"""\n\n
        Finished downloads: {status.finished_tasks_count}
        Failed downloads: {status.failed_tasks_count}
        -------------------------------------------------
        Time elapsed: {total_time_min:.2f} minutes
        """
        )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        asyncio.run(amain(event_loop=loop))
    except KeyboardInterrupt:
        print("Interrupted by user, downloads were cancelled")
    except aiohttp.web.HTTPNotFound:
        print("User/Collection not found, downloads were cancelled")
    except aiohttp.ClientResponseError as e:
        if e.status == http.HTTPStatus.TOO_MANY_REQUESTS:
            print("Too many requests error, downloads were cancelled")
            print("Please correct your limits and try again later.")
        else:
            print("Unknown error, downloads were cancelled")
            print("Status:", e.status)
    except aiohttp.ClientConnectionError:
        print("Internet connection issues, downloads were cancelled")
