import argparse
from .help_messages import *


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description=PROGRAM_DESCRIPTION)


parser.add_argument('--info', '-i',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_INFO)

parser.add_argument('--collections', '-c',
                    required=False,
                    type=str,
                    nargs='+',
                    action='append',
                    metavar='',
                    help=HELP_MSG_COLLECTIONS)

parser.add_argument('--uploads', '-u',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_UPLOADS)

parser.add_argument('--purity',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_PURITY)

parser.add_argument('--category',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_CATEGORY)

parser.add_argument('--sync', '-s',
                    required=False,
                    action="store_true",
                    help=HELP_MSG_SYNC)

parser.add_argument('--verbose', '-v',
                    required=False,
                    action="store_true",
                    help=HELP_MSG_VERBOSE)

parser.add_argument('--threads', '-t',
                    required=False,
                    type=int,
                    metavar='count',
                    help=HELP_MSG_THREADS)

args = vars(parser.parse_args())
