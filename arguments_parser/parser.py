import os
import argparse

import arguments_parser.help_messages as help_messages
from aiowallhaven.types.wallhaven_enums import Purity, Category
from aiowallhaven.types.wallhaven_types import PurityFilter, CategoryFilter
from wallpapers_downloader.downloader import CollectionTask, UploadTask

DEFAULT_DOWNLOADS_PATH = os.curdir + os.sep + "downloads"
COLLECTIONS_PATH = DEFAULT_DOWNLOADS_PATH + os.sep + "collections"
UPLOADS_PATH = DEFAULT_DOWNLOADS_PATH + os.sep + "uploads"

DEFAULT_THREADS_COUNT = 1
DEFAULT_VERBOSE = False

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description=help_messages.PROGRAM_DESCRIPTION,
)

# ------------- Arguments name for convenience
info_arg_name = "info"
collections_arg_name = "collections"
uploads_arg_name = "uploads"
purity_arg_name = "purity"
category_arg_name = "category"
sync_arg_name = "sync"
downloads_path_arg_name = "downloads_path"
verbose_arg_name = "verbose"
workers_arg_name = "workers"
api_key_arg_name = "api_key"

parser.add_argument(
    f"--{info_arg_name}",
    f"-{info_arg_name[0]}",
    type=str,
    nargs="+",
    metavar="",
    help=help_messages.HELP_MSG_INFO,
)

parser.add_argument(
    f"--{collections_arg_name}",
    f"-{collections_arg_name[0]}",
    type=str,
    nargs="+",
    action="append",
    metavar="",
    help=help_messages.HELP_MSG_COLLECTIONS,
)

parser.add_argument(
    f"--{uploads_arg_name}",
    f"-{uploads_arg_name[0]}",
    type=str,
    nargs="+",
    metavar="",
    help=help_messages.HELP_MSG_UPLOADS,
)

parser.add_argument(
    f"--{purity_arg_name}",
    type=str,
    nargs="+",
    metavar="",
    help=help_messages.HELP_MSG_PURITY,
)

parser.add_argument(
    f"--{category_arg_name}",
    type=str,
    nargs="+",
    metavar="",
    help=help_messages.HELP_MSG_CATEGORY,
)

parser.add_argument(
    f"--{sync_arg_name}",
    f"-{sync_arg_name[0]}",
    action="store_true",
    help=help_messages.HELP_MSG_SYNC,
)

parser.add_argument(
    f"--{downloads_path_arg_name}",
    f"-{downloads_path_arg_name[0]}",
    type=str,
    metavar="",
    default=DEFAULT_DOWNLOADS_PATH,
    help=help_messages.HELP_MSG_DOWNLOADS_PATH,
)

parser.add_argument(
    f"--{verbose_arg_name}",
    "-v",
    action="store_true",
    default=DEFAULT_VERBOSE,
    help=help_messages.HELP_MSG_VERBOSE,
)

parser.add_argument(
    f"--{workers_arg_name}",
    f"-{workers_arg_name[0]}",
    type=int,
    metavar="count",
    default=DEFAULT_THREADS_COUNT,
    help=help_messages.HELP_MSG_THREADS,
)


parser.add_argument(
    f"--{api_key_arg_name}",
    f"-{api_key_arg_name[0]}",
    type=str,
    metavar="",
)

args = vars(parser.parse_args())


def get_info_usernames():
    usernames = args[info_arg_name]
    if usernames is None:
        return []
    else:
        return usernames


def get_all_tasks() -> list[CollectionTask | UploadTask]:
    tasks = []

    # each collection is a list with first element as a username
    # and all others as its collections
    if args[collections_arg_name]:
        for collection in args[collections_arg_name]:
            tasks.append(
                CollectionTask(
                    username=collection[0],
                    collections=collection[1:],
                    save_directory=COLLECTIONS_PATH + os.sep + collection[0],
                )
            )

    # uploads arg is more simple - it's just a list o usernames
    if args[uploads_arg_name]:
        for upload in args[uploads_arg_name]:
            tasks.append(
                UploadTask(
                    username=upload, save_directory=UPLOADS_PATH + os.sep + upload
                )
            )

    return tasks


def get_purity_filter():
    if args[purity_arg_name] is None:
        return PurityFilter({Purity.sfw, Purity.sketchy, Purity.nsfw})

    purity_filter = PurityFilter()

    if "sfw" in args[purity_arg_name]:
        purity_filter.set_purity(Purity.sfw)
    if "sketchy" in args[purity_arg_name]:
        purity_filter.set_purity(Purity.sketchy)
    if "nsfw" in args[purity_arg_name]:
        purity_filter.set_purity(Purity.nsfw)
    return purity_filter


def get_category_filter():
    if args[category_arg_name] is None:
        return CategoryFilter({Category.general, Category.anime, Category.people})

    category_filter = CategoryFilter()

    if "general" in args[category_arg_name]:
        category_filter.set_category(Category.general)
    if "anime" in args[category_arg_name]:
        category_filter.set_category(Category.anime)
    if "people" in args[category_arg_name]:
        category_filter.set_category(Category.people)
    return category_filter


def get_downloads_path():
    return args[downloads_path_arg_name]


def get_logger_level():
    verbose = args[verbose_arg_name]
    if verbose:
        return "INFO"
    else:
        return "WARNING"


def get_workers_count():
    threads = args[workers_arg_name]
    if threads <= 0:
        threads = DEFAULT_THREADS_COUNT
    return threads


def get_api_key():
    return args[api_key_arg_name]
