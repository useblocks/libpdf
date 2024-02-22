"""Definition for PDF file."""

from typing import TYPE_CHECKING

from libpdf.models.file_meta import FileMeta
from libpdf.models.model_base import ModelBase
from libpdf.utils import string_to_identifier

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.root import Root  # pylint: disable=cyclic-import


# TODO the page cropping is defined by the user and must not be stored; the
#      current implementation is also not complete because it lacks the smart
#      ignore header/footer feature
class File(ModelBase):
    """
    PDF file data.

    There is a file wide crop feature that removes static parts from each page::

        *-page-------------------------------------*
        |                    ^                     |
        |                crop_top                  |
        |                    v                     |
        |               +-content-+                |
        |<--crop_left-->|         |<--crop_right-->|
        |               |         |                |
        |               |         |                |
        |               +---------+                |
        |                   ^                      |
        |              crop_bottom                 |
        |                   v                      |
        *------------------------------------------*

    It can be used to ignore headers, footers or sidebars.
    The user-defined parameters are exposed to both the CLI and API.

    :ivar name: PDF file name
    :vartype name: str
    :ivar path: PDF file path
    :vartype path: str
    :ivar page_count: number of pages in PDF
    :vartype page_count: int
    :ivar crop_top: distance in points from top of each page to ignore for extraction
    :vartype crop_top: float
    :ivar crop_bottom: distance in points from bottom of each page to ignore for extraction
    :vartype crop_bottom: float
    :ivar crop_left: distance in points from left side of each page to ignore for extraction
    :vartype crop_left: float
    :ivar crop_right: distance in points from right side of each page to ignore for extraction
    :vartype crop_right: float
    :ivar file_meta: reference to FileMeta instance
    :vartype file_meta: FileMeta
    :ivar b_root: back reference to Root instance
    :vartype b_root: Root
    """

    def __init__(
        self,
        name: str,
        path: str,
        page_count: int,
        crop_top: float = 0,
        crop_bottom: float = 0,
        crop_left: float = 0,
        crop_right: float = 0,
        file_meta: FileMeta = None,
        root: "Root" = None,
    ):
        """Initialize the instance."""
        self.name = name
        self.path = path
        self.page_count = page_count
        self.crop_top = crop_top
        self.crop_bottom = crop_bottom
        self.crop_left = crop_left
        self.crop_right = crop_right
        self.file_meta = file_meta
        self.b_root = root
        self.set_backref()

    def set_backref(self):
        """Set b_file property on FileMeta."""
        if self.file_meta is not None:
            self.file_meta.b_file = self

    @property
    def id_(self):
        """
        Return the identifier to address the file.

        The parameter can later be used during libpdf postprocessing to link to elements in other files.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used. The file identifier is built from the file name including extension. All characters are removed that
        do not follow the Python identifier character set (Regex character set ``[_a-zA-Z0-9]``).
        """
        return "file." + string_to_identifier(self.name)
