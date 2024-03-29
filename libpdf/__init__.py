"""
libpdf
~~~~~~

libpdf allows the extraction of structured data from technical PDFs.
It defines a generic class model of PDF documents and makes it available
through an API and also as a command line interface.

:copyright: © 2024 by team useblocks
:license: MIT, see LICENSE for more details
"""  # noqa: D205, D400, D415 # needed for autodoc

import importlib.metadata as importlib_metadata

__version__: str = importlib_metadata.version("libpdf")
__summary__: str = importlib_metadata.metadata("libpdf")["Summary"]

# below imports from libpdf.core cannot be at the top avoid circular import errors in
# core.py when importing __version__ and __summary__
import libpdf._import_forks  # noqa: F401
from libpdf.core import main_api as load
from libpdf.core import main_cli

# define importable objects
__all__ = ["__summary__", "__version__", "load"]

# Enable running
#   python -m libpdf.__init__
#   python libpdf/__init__.py
# before installing the package itself
if __name__ == "__main__":
    main_cli()
