"""Definition for PDF chapters."""

from typing import TYPE_CHECKING, List, Union

from libpdf.models.element import Element
from libpdf.models.horizontal_box import HorizontalBox

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.figure import Figure  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports
    from libpdf.models.paragraph import Paragraph  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports
    from libpdf.models.position import Position  # pylint: disable=cyclic-import, ungrouped-imports
    from libpdf.models.table import Table  # noqa: F401  # pylint: disable=cyclic-import, ungrouped-imports


class Chapter(Element):
    """
    PDF chapter (extracted from PDF outline).

    The Chapter elements defines the structure of the PDF. If an outline is given, Chapters are extracted from it
    and all elements (sub-chapters, tables, figures, paragraphs) are put below the Chapter in the ordered content list.

    :ivar title: the title of the chapter, as extracted from outline
    :vartype title: str
    :ivar number: the chapter number as string (e.g. '3.2.4')
    :vartype number: str
    :ivar textbox: the textbox of the chapter, as extracted from pdfminer
    :vartype textbox: HorizontalBox
    :ivar number: the chapter number as string (e.g. '3.2.4')
    :vartype number: str
    :ivar position: a Position instance determining the location of the Chapter;
                    a Chapter commonly spans across several pages, however only one Position is aggregated
                    because the end of the Chapter can be determined by looking at the next Chapter
    :vartype position: Position
    :ivar content: the content of the chapter (other sub-chapters, paragraphs, tables, figures)
    :vartype content: List[Union[Chapter, Paragraph, Table, Figure]]
    """

    def __init__(
        self,
        title: str,
        number: str,
        position: 'Position',
        content: List[Union['Chapter', 'Paragraph', 'Table', 'Figure']] = None,
        chapter: 'Chapter' = None,
        textbox: HorizontalBox = None,
    ):
        """Initialize the instance."""
        super().__init__(position=position, chapter=chapter)
        self.title = title
        self.number = number
        self.textbox = textbox
        self.content = [] if content is None else content
        self.set_backref()

    @property
    def id_(self):
        """
        Return the identifier to address the Chapter.

        The identifier follows the pattern ``chapter.<number>``.

        It is used as a link target if a PDF link-annotation points to the Element.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used.

        :type: str
        """
        return f'chapter.{self.number}'

    def set_backref(self):
        """Set b_chapter property on all elements under contents."""
        for element in self.content:
            element.b_chapter = self

    def __repr__(self):
        """
        Return a chapter title with its index number.

        The purpose of it is to improve the readability in the debugger.
        """
        return f'{self.number} {self.title}'
