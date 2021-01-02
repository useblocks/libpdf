"""Definition for PDF linked text."""
from typing import Dict, TYPE_CHECKING, Union

from libpdf.models.model_base import ModelBase

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.table import Cell  # noqa: F401  # pylint: disable=cyclic-import
    from libpdf.models.figure import Figure  # noqa: F401  # pylint: disable=cyclic-import
    from libpdf.models.paragraph import Paragraph  # noqa: F401  # pylint: disable=cyclic-import


class Link(ModelBase):
    """
    PDF link embedded in the text.

    :ivar idx_start: the 0-based index of the start char. This char is included in the link text.
    :vartype idx_start: int
    :ivar idx_stop: the 0-based index of the stop char. This char is excluded in the link text, so
                    the start/stop indexes are compatible with the Python string slicing notation.
    :vartype idx_stop: int
    :ivar pos_target: the position where the link points to. e.g ``{'page': 4, 'x': 56, 'y': 789}``
    :vartype pos_target: Dict[str, float]
    :ivar libpdf_target: points either to a libpdf :class:`~libpdf.models.element.Element` or
            to a :class:`~libpdf.models.page.Page`. The libpdf :class:`~libpdf.models.element.Element` link is built
            by concatenating nested elements, separated by '/', e.g. ``chapter.3/chapter.3.2/table.2``.
            In case ``pos_target`` cannot be resolved to a libpdf :class:`~libpdf.models.element.Element`,
            the target is set to the target coordinates given as ``page.<id>/<X>:<Y>``, e.g.
            ``page.4/56:789``. In this case ``libpdf_target`` is identical to ``pos_target``.
    :vartype libpdf_target: str
    :ivar b_source: back reference to the link source, can be :class:`~libpdf.models.paragraph.Paragraph`,
                    :class:`~libpdf.models.figure.Figure` or :class:`~libpdf.models.table.Cell`
    """

    def __init__(
        self,
        idx_start: int,
        idx_stop: int,
        pos_target: Dict,
        libpdf_target: str = None,
        b_source: Union['Paragraph', 'Figure', 'Cell'] = None,
    ):
        """Initialize the instance."""
        self.idx_start = idx_start
        self.idx_stop = idx_stop
        self.pos_target = pos_target
        self.libpdf_target = libpdf_target
        self.b_source = b_source

    @property
    def source_chars(self):
        """
        Show the text between the start and stop indices.

        Main usecase for this is debugging.
        """
        if self.b_source:
            # Black8 is contradictory to pylint E203 whitespace before ':'
            # fmt: off
            extracted_text = self.b_source.text[self.idx_start: self.idx_stop]
            # fmt: on
            return extracted_text
        return None

    def __repr__(self):
        """Make link of the repr for better debugging."""
        return f'{self.source_chars}'
