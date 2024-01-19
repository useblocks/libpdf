"""Definition for PDF elements."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from libpdf.models.model_base import ModelBase

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.chapter import (
        Chapter,  # pylint: disable=cyclic-import
    )
    from libpdf.models.position import (
        Position,  # pylint: disable=cyclic-import
    )
    from libpdf.models.root import Root  # pylint: disable=cyclic-import


# need to ignore flake8 errors because sphinx.autodoc sees the multiline as one line. It is actually the summary line.
class Element(ModelBase, ABC):
    """
    Base class for :class:`~libpdf.models.chapter.Chapter`,
    :class:`~libpdf.models.paragraph.Paragraph`, :class:`~libpdf.models.table.Table` and
    :class:`~libpdf.models.figure.Figure`.

    :ivar position: a Position instance determining the location of the Element
    :vartype position: Position
    :ivar b_root: Root instance (mutually exclusive with the b_chapter parameter)
    :vartype b_root: Root
    :ivar b_chapter: parent Chapter instance (mutually exclusive with the b_root parameter)
    :vartype b_chapter: Chapter
    """  # noqa: D205

    def __init__(
        self,
        position: "Position",
        root: "Root" = None,
        chapter: "Chapter" = None,
    ):
        """Initialize the instance."""
        self.type = self.__class__.__name__.lower()
        self.position = position
        self.b_root = root
        self.b_chapter = chapter
        self.set_position_backref()
        self.position.page.content.append(self)

    def set_position_backref(self):
        """Set b_element property on self.position members."""
        if self.position is not None:
            self.position.b_element = self

    @property
    @abstractmethod
    def id_(self):
        """Return the identifier to address the Element."""
        return

    @property
    def uid(self):
        """
        Return the unique identifier to address the full path to the Element.

        The identifier follows the pattern ``element.<number>/element.<number>``.

        For example, the uid for a paragraph in chapter.2.1.4 is 'chapter.2/chapter.2.1/chapter.2.1.4/paragraph.6'.

        :type: str
        """
        if self.b_chapter:
            curr_chapter = self.b_chapter
            uid_prefix = curr_chapter.id_
            while curr_chapter.b_chapter:
                uid_prefix = curr_chapter.b_chapter.id_ + "/" + uid_prefix
                curr_chapter = curr_chapter.b_chapter
            uid = f"{uid_prefix}/{self.id_}"
        else:
            uid = f"{self.id_}"

        return uid

    def contains_coord(self, page: int, x: float, y: float):
        """
        Return True if coordinate x,y is contained in the element's position bbox else False.

        This can be used to determine whether a link target points to this element.

        :param page: page number
        :param x: x coordinate of a link
        :param y: y coordinate of a link
        :return: True if coordinate x,y is contained in the Element else False
        """
        return self.position.contains_coord(page, x, y)
