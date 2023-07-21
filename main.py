import os

import aiohttp
from dotenv import load_dotenv

import arguments_parser.parser as arg_parser
from aiowallhaven.types.wallhaven_types import SearchFilter
from wallpapers_downloader.downloader import WallhavenDownloader

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
    if not any(arg_parser.args.values()):
        arg_parser.parser.print_usage()
        exit()

    search_filter = SearchFilter(
        category=arg_parser.get_category_filter(),
        purity=arg_parser.get_purity_filter(),
    )

    downloader = WallhavenDownloader(
        api_key=WALLHAVEN_API_KEY,
        downloads_directory=arg_parser.get_downloads_path(),
        tasks=arg_parser.get_all_tasks(),
        workers_count=arg_parser.get_workers_count(),
        downloads_filters=search_filter,
    )

    if arg_parser.get_info_usernames():
        await downloader.print_users_info(arg_parser.get_info_usernames())
    else:
        await downloader.run_downloader()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        asyncio.run(amain(event_loop=loop))
    except aiohttp.ClientResponseError as e:
        print(f"Response error with status {e.status}")
        print(f"Task info: {e.request_info.url}")
    except aiohttp.ClientError:
        print("Connection issues, downloads were cancelled")
    except KeyboardInterrupt:
        print("Interrupted by user, downloads were cancelled")
