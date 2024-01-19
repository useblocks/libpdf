"""
Log configuration.

Logging advice given here is followed
https://www.geeksforgeeks.org/python-add-logging-to-python-libraries/
"""

import logging
import math

from libpdf.progress import TQDM_AVAILABLE, tqdm


def get_level_name(verbose):
    """Return the log levels for the CLI verbosity flag in words."""
    verbose = min(verbose, 3)
    level_dict = {
        0: "ERROR/FATAL/CRITICAL",
        1: "WARNING",
        2: "INFO",
        3: "DEBUG",
    }
    return level_dict[verbose]


class TqdmLoggingHandler(logging.Handler):
    """
    A custom logging handler to output log messages through tqdm.write.

    This is needed to correctly interact tqdm progress bars with log messages.
    See https://github.com/tqdm/tqdm/issues/313#issuecomment-347960988.
    """

    def __init__(self, level=logging.DEBUG):  # pylint: disable=useless-super-delegation
        """Call parent init method."""
        # pylint has a bug here because overriding the method is actually not useless due to a differing default
        # value for level parameter
        # looks like this one: https://github.com/PyCQA/pylint/issues/1085
        super().__init__(level)

    def emit(self, record):
        """Log the record through tqdm.write."""
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # only these 2 exceptions should be raised to the terminal, so an immediate raise is needed to split them
            # from others
            raise
        except Exception:  # pylint: disable=broad-except
            # logger does not know what exceptions may come but still has to handle them
            self.handleError(record)


def config_logger(cli=True):
    """
    Initialize the logger for both API and CLI usage.

    For API usage the handler init depends on the availability of tqdm.
    tqdm needs to output through a logging handler to correctly interact with the other log messages of the library.
    See https://github.com/tqdm/tqdm/issues/313#issuecomment-347960988.

    For CLI usage the handler is always initialized, if tqdm is available it gets a special TQDM handler, if not
    only basic init is done.
    """
    init_basic = False
    init_tqdm = False
    if cli:
        if TQDM_AVAILABLE:
            init_tqdm = True
        else:
            init_basic = True
    else:  # API usage
        if TQDM_AVAILABLE:
            # this needs to be documented so any API user is not surprised that the libpdf logger has an attached
            # handler; users may delete it if unwanted or it could be configurable later if tqdm handler should be
            # used or the user wants to define something else
            init_tqdm = True
        else:  # don't init anything, it's up to the user
            pass

    log_format = "[%(levelname)5s] %(name)s - %(message)s"
    if init_tqdm:
        root_logger = logging.getLogger()
        handler = TqdmLoggingHandler(
            level=logging.DEBUG
        )  # output all messages, log level handling is done in logger
        handler.formatter = logging.Formatter(log_format)
        root_logger.addHandler(handler)
    if init_basic:
        logging.basicConfig(format=log_format)


def set_log_level(verbose):
    """
    Set the log level according to the CLI verbosity flag.

    All loggers have libpdf as a parent, setting the log level for libpdf also affects all child loggers like
    libpdf.core.
    """
    log = logging.getLogger("libpdf")
    if verbose == 0:
        log.setLevel("ERROR")
    elif verbose == 1:
        log.setLevel("WARNING")
    elif verbose == 2:
        log.setLevel("INFO")
    else:
        log.setLevel("DEBUG")


def logging_needed(idx_page: int, count_pages: int):
    """
    Determine if logging is needed for the current page.

    A log messages shall be emitted every 20% of pages.
    """
    if TQDM_AVAILABLE:
        return False
    twenty_percent = count_pages / 5.0
    round_up_next_ten = int(math.ceil(twenty_percent / 10.0)) * 10
    return (
        idx_page == 0
        or (idx_page + 1) % round_up_next_ten == 0
        or idx_page == count_pages - 1
    )
