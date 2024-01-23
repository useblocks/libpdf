"""Definition for PDF rects."""
from __future__ import annotations

from typing import TYPE_CHECKING

from libpdf.models.element import Element

if TYPE_CHECKING:
    from libpdf.models.horizontal_box import HorizontalBox
    from libpdf.models.link import Link
    from libpdf.models.position import (
        Position,
    )


class Rect(Element):
    """PDF Rect."""

    def __init__(
        self,
        idx: int,
        position: Position,
        links: list[Link],
        textboxes: list[HorizontalBox],
        non_stroking_color: tuple | None = None,
    ):
        """Initialize the instance."""
        super().__init__(position=position)
        self.idx = idx
        self.textboxes = textboxes
        self.links = links
        self.non_stroking_color = non_stroking_color
        if self.links:
            self._set_links_backref()

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

    def _set_links_backref(self) -> None:
        """Set b_source back reference on all links."""
        for link in self.links:
            link.b_source = self
