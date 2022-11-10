import argparse
from .help_messages import *


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                 description=PROGRAM_DESCRIPTION,
                                 )

parser.add_argument('-i', '--info',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_INFO
                    )

parser.add_argument('-c', '--collections',
                    required=False,
                    type=str,
                    nargs='+',
                    action='append',
                    metavar='',
                    help=HELP_MSG_COLLECTIONS
                    )

parser.add_argument('-u', '--uploads',
                    required=False,
                    type=str,
                    nargs='+',
                    metavar='',
                    help=HELP_MSG_UPLOADS
                    )


parser.add_argument('-s', '--sync',
                    required=False,
                    action="store_true",
                    help=HELP_MSG_SYNC
                    )

parser.add_argument('-v', '--verbose',
                    required=False,
                    action="store_true",
                    help=HELP_MSG_VERBOSE
                    )

parser.add_argument('-p', '--parallel',
                    required=False,
                    type=int,
                    metavar='',
                    help=HELP_MSG_PARALLEL
                    )


args = vars(parser.parse_args())
