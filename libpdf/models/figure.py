"""Definition for PDF figures."""

from typing import TYPE_CHECKING, List

from libpdf.models.element import Element
from libpdf.models.horizontal_box import HorizontalBox
from libpdf.models.link import Link

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.position import (
        Position,  # , pylint: disable=ungrouped-imports
    )


class Figure(Element):
    """
    PDF figure.

    A figure can be a bitmap image or vector graphics mixed with overlaying text.
    libpdf extracts figures into an external file where ``rel_path`` defines the path to the external file.
    The text property contains text extracted from the figure area. This can be highly unstructured because
    libpdf does not analyze the text layout within figures as there is no common denominator for an algorithm.
    libpdf will however do the same character grouping analysis as for paragraphs,
    so the user can assume text flow is from top left to bottom right.

    :ivar idx: the number of the instance in the current scope, 1-based
    :vartype idx: int
    :ivar rel_path: the path to the external file containing the figure
    :vartype rel_path: str
    :ivar textboxes: the textboxes of the figure, as extracted from pdfminer
    :vartype textboxes: a list of HorizontalBox
    :ivar caption: the caption of the figure (text over/under the figure describing it)
    :vartype caption: str
    :ivar position: a Position instance determining the location of the figure
    :vartype position: Position
    :ivar links: list of text links in the figure area
    :vartype links: List[Link]
    """

    def __init__(
        self,
        idx: int,
        rel_path: str,
        position: "Position",
        links: List[Link],
        textboxes: List[HorizontalBox],
        text: str = None,
        caption: str = None,
    ):
        """Initialize the instance."""
        super().__init__(position=position)
        self.idx = idx
        self.rel_path = rel_path
        self.text = text
        self.textboxes = textboxes
        self.links = links
        self.caption = caption
        if self.links:
            self.set_links_backref()

    @property
    def id_(self):
        """
        Return the identifier to address the Figure.

        The identifier follows the pattern ``figure.<idx>``.
        idx the 1-based number of the Figure in the current scope (root, chapter, sub-chapters, page).

        It is used as a link target if a PDF link-annotation points to the Element.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used.

        :type: str
        """
        return f"figure.{self.idx}"

    def set_links_backref(self):
        """Set b_source back reference on all links."""
        for link in self.links:
            link.b_source = self
