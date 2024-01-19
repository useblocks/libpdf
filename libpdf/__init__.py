"""
libpdf
~~~~~~

libpdf allows the extraction of structured data from technical PDFs.
It defines a generic class model of PDF documents and makes it available
through an API and also as a command line interface.

:copyright: © 2020 by team useblocks
:license: MIT, see LICENSE for more details
"""  # needed for autodoc
try:
    import importlib_metadata  # Python 3.6 and 3.7
except ImportError:
    import importlib.metadata as importlib_metadata  # Python 3.8, 3.9

__version__: str = importlib_metadata.version("libpdf")
__summary__: str = importlib_metadata.metadata("libpdf")["Summary"]

# below imports from libpdf.core cannot be at the top avoid circular import errors in core.py when
# importing __version__ and __summary__
import libpdf._import_forks  # noqa: F401
from libpdf.core import main_api as load
from libpdf.core import main_cli

# define importable objects
__all__ = ["load", "__version__", "__summary__"]

# Enable running
#   python -m libpdf.__init__
#   python libpdf/__init__.py
# before installing the package itself
if __name__ == "__main__":
    main_cli()
