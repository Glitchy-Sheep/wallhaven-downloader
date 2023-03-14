import os
import argparse

import arguments_parser.help_messages as help_messages
from aiowallhaven.wallhaven_types import Purity, Category
from wallpapers_downloader.downloader import CollectionTask, UploadTask

DEFAULT_DOWNLOADS_PATH = os.curdir + os.sep + "downloads"
COLLECTIONS_PATH = DEFAULT_DOWNLOADS_PATH + os.sep + 'collections'
UPLOADS_PATH = DEFAULT_DOWNLOADS_PATH + os.sep + 'uploads'

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description=help_messages.PROGRAM_DESCRIPTION)


parser.add_argument('--info', '-i',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=help_messages.HELP_MSG_INFO)

parser.add_argument('--collections', '-c',
                    required=False,
                    type=str,
                    nargs='+',
                    action='append',
                    metavar='',
                    help=help_messages.HELP_MSG_COLLECTIONS)

parser.add_argument('--uploads', '-u',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=help_messages.HELP_MSG_UPLOADS)

parser.add_argument('--purity',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=help_messages.HELP_MSG_PURITY)

parser.add_argument('--category',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=help_messages.HELP_MSG_CATEGORY)

parser.add_argument('--sync', '-s',
                    required=False,
                    action="store_true",
                    help=help_messages.HELP_MSG_SYNC)

parser.add_argument('--downloads-path', '-d',
                    required=False,
                    type=str,
                    metavar='',
                    default=DEFAULT_DOWNLOADS_PATH,
                    help=help_messages.HELP_MSG_DOWNLOADS_PATH)

parser.add_argument('--verbose', '-v',
                    required=False,
                    action="store_true",
                    help=help_messages.HELP_MSG_VERBOSE)

parser.add_argument('--threads', '-t',
                    required=False,
                    type=int,
                    metavar='count',
                    help=help_messages.HELP_MSG_THREADS)


args = vars(parser.parse_args())


def get_purity_filter():
    if args['purity'] is None:
        return Purity(True, True, True)

    purity_filter = Purity(False, False, False)

    if "sfw" in args['purity']:
        purity_filter.sfw = True
    if "sketchy" in args['purity']:
        purity_filter.sketchy = True
    if "nsfw" in args['purity']:
        purity_filter.nsfw = True
    return purity_filter


def get_category_filter():
    if args['category'] is None:
        return Category(True, True, True)

    category_filter = Category(False, False, False)

    if "general" in args['category']:
        category_filter.general = True
    if "anime" in args['category']:
        category_filter.anime = True
    if "people" in args['category']:
        category_filter.people = True
    return category_filter


def get_downloads_path():
    return args['downloads_path']


def get_all_tasks() -> list[CollectionTask | UploadTask]:
    tasks = []

    # each collection is a list with first element as a username
    # and all others as its collections
    if args['collections']:
        for collection in args['collections']:
            tasks.append(CollectionTask(
                username=collection[0],
                collections=collection[1:],
                save_directory=COLLECTIONS_PATH + os.sep + collection[0]))

    # uploads arg is more simple - it's just a list o usernames
    if args['uploads']:
        for upload in args['uploads']:
            tasks.append(UploadTask(
                username=upload[0],
                save_directory=UPLOADS_PATH + os.sep + upload[0]))

    return tasks
