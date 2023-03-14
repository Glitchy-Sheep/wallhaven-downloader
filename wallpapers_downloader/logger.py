import logging
import arguments_parser.parser as arg_parser


# for future use
def get_downloader_logger():
    logger = logging.getLogger(__name__)
    log_level = arg_parser.get_logger_level()
