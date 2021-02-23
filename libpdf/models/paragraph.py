"""Definition for PDF textblocks."""
from typing import List, TYPE_CHECKING

from libpdf.models.element import Element
from libpdf.models.horizontal_box import HorizontalBox
from libpdf.models.link import Link


# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.chapter import Chapter  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports
    from libpdf.models.position import Position  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports
    from libpdf.models.root import Root  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports


class Paragraph(Element):
    r"""
    PDF paragraph (normal text).

    A paragraph always ends at the end of a page.

    :ivar idx: the number of the instance in the current scope, 1-based
    :vartype idx: int
    :ivar position: the position of the paragraph
    :vartype position: Position
    :ivar links: list of links in the paragraph text
    :vartype links: List[Link]
    :ivar textbox: the textbox of the paragraph, as extracted from pdfminer
    :vartype textbox: HorizontalBox
    """

    def __init__(
        self,
        idx: int,
        position: 'Position',
        links: List[Link],
        textbox: HorizontalBox = None,
        root: 'Root' = None,
        chapter: 'Chapter' = None,
    ):
        """Initialize the instance."""
        super().__init__(position=position, root=root, chapter=chapter)
        self.links = links
        self.idx = idx
        self.textbox = textbox
        if self.links:
            self.set_links_backref()

    @property
    def id_(self):
        """
        Return the identifier to address the Paragraph.

        The identifier follows the pattern ``paragraph.<idx>``.
        idx the 1-based number of the Paragraph in the current scope (root, chapter, sub-chapters, page).

        It is used as a link target if a PDF link-annotation points to the Element.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used.

        :type: str
        """
        return f'paragraph.{self.idx}'

    def set_links_backref(self):
        """Set b_source back reference on all links."""
        for link in self.links:
            link.b_source = self

    def __repr__(self):
        """Make paragraph text part of the repr for better debugging."""
        return f'{type(self).__name__}({self.id_})({self.textbox.text})'
