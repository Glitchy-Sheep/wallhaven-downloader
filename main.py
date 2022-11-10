import os
import asyncio
import logging
import time

from modules.arguments_parser.parser import args
from modules.downloader.downloader import WallhavenDownloader

LOG = logging.getLogger(__name__)

WALLHAVEN_API_KEY = os.getenv("WALLHAVEN_API_KEY")
if not WALLHAVEN_API_KEY:
    WALLHAVEN_API_KEY = ""


async def amain(event_loop):
    log_level = "INFO" if args['verbose'] else "WARNING"
    parallel_n = args['parallel'] if args['parallel'] else 1
    if parallel_n < 1:
        parallel_n = 1

    d = WallhavenDownloader(
        WALLHAVEN_API_KEY, async_downloads=parallel_n, log_level=log_level)
    await d.add_tasks(
        args["collections"],
        args["uploads"]
    )
    await d.perform_tasks()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        start_time = time.time()
        asyncio.run(amain(event_loop=loop))
        end_time = time.time()
        print(f"All tasks finished. Elapsed time: {end_time - start_time}")
    except KeyboardInterrupt:
        print("Interrupted by user")
