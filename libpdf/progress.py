"""Handle progress bars using tqdm."""
import logging

LOG = logging.getLogger(__name__)

TQDM_AVAILABLE = False
COLORAMA_AVAILABLE = False

# handle optional dependency tqdm for progress bars
try:
    # the import is not used within this module but imported by others
    # the idea is to centralize the importing of tqdm to have a common graceful fallback if it's not installed
    from tqdm import tqdm  # pylint: disable=import-error,unused-import

    TQDM_AVAILABLE = True
except ImportError:

    # class name is constrained by the tqdm library
    class tqdm:  # pylint: disable=invalid-name
        """Mock tqdm.tqdm class and provide the least amount of functionality."""

        def __init__(self, iterable=None, **kwargs):
            """Set iterable to the class for later usage in __iter__."""
            del kwargs  # delete parameter to denote the information is not used
            self.iterable = iterable

        def __iter__(self):
            """
            Iterate over self.iterable.

            This is the main method of the tqdm class, it just wraps the iterator so it's transparent from callers'
            perspective.
            """
            # Inlining instance variables as locals (speed optimisation)
            iterable = self.iterable

            for obj in iterable:
                yield obj

        def __enter__(self):
            """Enable using tqdm as context manager."""
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            """Enable using tqdm as context manager."""

        @staticmethod
        def update(*args, **kwargs):
            """Mock the tqdm.update function to manually update progress bars."""
            del args, kwargs  # delete parameters to denote the information is not used

        @staticmethod
        def write(*args, **kwargs):
            """Mock the tqdm.write function to write log messages through tqdm."""
            del args, kwargs  # delete parameters to denote the information is not used


# handle optional dependency colorama for colored progress bars
try:
    from colorama import Fore  # pylint: disable=import-error

    COLORAMA_AVAILABLE = True
except ImportError:

    class CatchAllAttributesType(type):
        """
        A metaclass to catch all static class variables and return an empty string for them.

        See https://stackoverflow.com/a/3155493
        """

        def __getattr__(cls, key):
            """Return an empty string for all class attributes if used as a metaclass."""
            return ''

    class Fore(metaclass=CatchAllAttributesType):  # pylint: disable=too-few-public-methods
        """
        Mock colorama.Fore and return only an empty string.

        The colors are used in tqdm.tqdm(bar_format) parameter and setting an empty string lead to the string
        not containing ANSI codes after injecting the parameters.
        """


# all libpdf modules should only access tqdm and colorama through this module
# COLOR_MAP is used to decouple from colorama.Fore which could be a missing dependency
COLOR_MAP = {
    'black': Fore.BLACK,
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'blue': Fore.BLUE,
    'magenta': Fore.MAGENTA,
    'cyan': Fore.CYAN,
    'white': Fore.WHITE,
    'reset': Fore.RESET,
}


def bar_format(color):
    """Return a colored tqdm bar_format argument template."""
    return f"{COLOR_MAP[color]}{{l_bar}}{{bar}}{{r_bar}}{COLOR_MAP['reset']}"


def bar_format_lvl0():
    """bar_format for the top level instance of nested tqdm progress bars."""
    return bar_format('red')


def bar_format_lvl1():
    """bar_format for the 1st level instance of nested tqdm progress bars."""
    return bar_format('cyan')


def bar_format_lvl2():
    """bar_format for the 2nd level instance of nested tqdm progress bars."""
    return bar_format('green')
