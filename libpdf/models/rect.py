"""Definition for PDF figures."""
from typing import TYPE_CHECKING, List

from libpdf.models.element import Element
from libpdf.models.horizontal_box import HorizontalBox
from libpdf.models.link import Link

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.position import Position  # noqa: F401, pylint: disable=ungrouped-imports


class Rect(Element):
    """
    PDF Rect.
    """

    def __init__(
        self,
        idx: int,
        position: 'Position',
        links: List[Link],
        textboxes: List[HorizontalBox],
        non_stroking_color: str = None,
    ):
        """Initialize the instance."""
        super().__init__(position=position)
        self.idx = idx
        self.textboxes = textboxes
        self.links = links
        self.non_stroking_color = non_stroking_color
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
        return f'rect.{self.idx}'

    def set_links_backref(self):
        """Set b_source back reference on all links."""
        for link in self.links:
            link.b_source = self
