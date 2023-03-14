import logging
from arguments_parser.parser import args


# for future use
def get_downloader_logger():
    logger = logging.getLogger(__name__)
    log_level = "INFO" if args['verbose'] else "WARNING"
