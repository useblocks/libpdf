"""Definition of the abstract class of coordinates."""

from typing import List


class Coord:
    """
    Define the coordinates inherited by of :class:`~libpdf.models.position.Position`.

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
    """

    def __init__(
        self,
        x0: float = None,
        y0: float = None,
        x1: float = None,
        y1: float = None,
    ):
        """Init the class with rectangular coordinates."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
