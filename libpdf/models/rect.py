"""Definition for PDF rects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libpdf.models.element import Element
from libpdf.models.horizontal_box import HorizontalBox

if TYPE_CHECKING:
    from libpdf.models.horizontal_box import HorizontalBox
    from libpdf.models.position import (
        Position,
    )


class Rect(Element):
    """
    Rectangles in a PDF.

    The rectangles are extracted from pdfplumber.
    The text covered in the rectangle is extracted and
    stored in an newly instantiated textbox.
    """

    def __init__(
        self,
        idx: int,
        position: Position,
        textbox: HorizontalBox,
        non_stroking_color: tuple = None,
    ):
        super().__init__(position=position)
        self.idx = idx
        self.textbox = textbox
        self.non_stroking_color = non_stroking_color

    @property
    def id_(self) -> str:
        """
        Return the identifier to address the Figure.

        The identifier follows the pattern ``figure.<idx>``.
        idx the 1-based number of the Figure in the current scope
        (root, chapter, sub-chapters, page).

        It is used as a link target if a PDF link-annotation points to the Element.

        According to PDF model the parameter should be called ``id`` but the name is
        reserved in Python, so ``id_`` is used.

        :type: str
        """
        return f"rect.{self.idx}"
