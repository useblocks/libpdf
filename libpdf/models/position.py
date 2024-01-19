"""Definition of positions in the PDF."""
from typing import TYPE_CHECKING

from libpdf.parameters import TARGET_COOR_TOLERANCE

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.element import (
        Element,  # pylint: disable=cyclic-import
    )
    from libpdf.models.page import Page  # pylint: disable=cyclic-import
    from libpdf.models.table import Cell  # pylint: disable=cyclic-import


class Position:
    """
    Define the coordinates of an :class:`~libpdf.models.element.Element` or :class:`~libpdf.models.table.Cell`.

    A position is either linked by an Element or by a Cell (mutually exclusive).
    A position keeps a reference to the :class:`~libpdf.models.page.Page` it is located on.

    Here is some ASCII art to explain the libpdf coordinates::

        *-page------------------------*
        |                             |
        |                             |
        |                             |
        |        +-bbox----+          |
        |<--x0-->|         |    ^     |
        |        |         |    |     |
        |<-------|---x1--->|    |     |
        |        +---------+    |     |
        |            ^          |     |
        |           y0         y1     |
        |            v          v     |
        *-----------------------------*

    The bbox definition [x0, y0, x1, y1] is in sync with pdfminer and the PDF standard. Coordinate type is float for
    both libpdf and pdfminer.

    .. note::
        pdfplumber has a different definition of bounding boxes::

            *-page------------------------*
            |                ^      ^     |
            |               top     |     |
            |                v      |     |
            |        +-bbox----+    |     |
            |<--x0-->|         |    |     |
            |        |         |  bottom  |
            |<-------|---x1--->|    |     |
            |        +---------+    v     |
            |                             |
            |                             |
            |                             |
            *-----------------------------*

        The pdfplumber bounding box is [x0, top, x1, bottom]. Coordinate type is Decimal.

    To deal with the coordinate and type differences there are conversion functions ``to_pdfplumber_bbox`` and
    ``from_pdfplumber_bbox`` in module libpdf.utils.

    :ivar x0: distance from the left of the page to the left edge of the box
    :vartype x0: float
    :ivar y0: distance from the bottom of the page to the lower edge of the box (less than y1)
    :vartype y0: float
    :ivar x1: distance from the left of the page to the right edge of the box
    :vartype x1: float
    :ivar y1: distance from the bottom of the page to the upper edge of the box (greater than y0)
    :vartype y1: float
    :ivar page: reference to a Page object
    :vartype page: Page
    :ivar element: element that refers to the position (mutually exclusive with cell)
    :vartype element: Element
    :ivar cell: cell that refers to the position (mutually exclusive with element)
    :vartype cell: Cell
    """

    def __init__(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        page: "Page",
        element: "Element" = None,
        cell: "Cell" = None,
    ):
        """Init the class with rectangular coordinates and a page reference."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.page = page
        self.b_element = element
        self.b_cell = cell
        self.page.b_positions.append(self)

    def contains_coord(self, page: int, x: float, y: float) -> bool:
        """
        Return True if coordinate x,y is contained in the position else False.

        This can be used to determine whether a link target points to this element.

        :param page: page number
        :param x: x coordinate of a link
        :param y: y coordinate of a link
        :return: True if coordinate x,y is contained in the position else False
        """
        # assumption is target coordinates are always on the top-left of the element
        return (
            page == self.page.number
            and self.x1 > x >= (self.x0 - TARGET_COOR_TOLERANCE)
            and (self.y1 + TARGET_COOR_TOLERANCE) > y >= self.y0
        )

    def __repr__(self):
        """Return object representation including referenced type, page and bounding box."""
        # either of the 2 must be given
        if self.b_element is not None:
            ref_type = self.b_element
        else:
            ref_type = self.b_cell

        return f"Page {self.page.number} [{self.x0}, {self.y0}, {self.x1}, {self.y1}] ({ref_type})"
