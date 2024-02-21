"""Definition for PDF pages."""

from typing import TYPE_CHECKING, List, Union

from libpdf.models.model_base import ModelBase

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.chapter import (
        Chapter,  # pylint: disable=cyclic-import
    )
    from libpdf.models.figure import (
        Figure,  # pylint: disable=cyclic-import
    )
    from libpdf.models.paragraph import (
        Paragraph,  # pylint: disable=cyclic-import
    )
    from libpdf.models.position import (
        Position,  # pylint: disable=cyclic-import
    )
    from libpdf.models.root import Root  # pylint: disable=cyclic-import
    from libpdf.models.table import Table  # pylint: disable=cyclic-import


class Page(ModelBase):
    """
    PDF page data.

    :ivar number: PDF page number, 1-based
    :vartype number: int
    :ivar width: page width in points
    :vartype width: float
    :ivar height: page height in points
    :vartype height: float
    :ivar content: ordered list of elements on the page; chapters might still be nested if the page contains
                   sub-chapters
    :vartype content: List[Union[Chapter, Paragraph, Table, Figure]]
    :ivar root: back reference to a Root instance
    :vartype root: Root
    :ivar b_positions: back reference to all Position instances on the page
    :vartype b_positions: List[Position]
    """

    def __init__(
        self,
        number,
        width,
        height,
        content: List[Union["Chapter", "Paragraph", "Table", "Figure"]] = None,
        root: "Root" = None,
        positions: List["Position"] = None,
    ):
        """Initialize the instance."""
        self.number = number
        self.width = width
        self.height = height
        self.content = [] if content is None else content
        self.b_root = root
        self.b_positions = [] if positions is None else positions

    @property
    def id_(self):
        """
        Return the identifier to address the Page.

        The identifier follows the pattern ``page.<number>``.
        It is used as a link target if a PDF link annotation points to a blank space position, i.e. there is no
        Chapter, Paragraph, Table, Figure at the target location.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used.
        """
        return f"page.{self.number!s}"

    def __repr__(self):
        """Page representation using page.<number>."""
        return self.id_
