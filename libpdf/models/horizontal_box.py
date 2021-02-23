"""Definition of HorizontalBox to contain text in the PDF."""

from typing import List

from libpdf.models.coord import Coord


class TextBase:  # pylint: disable=too-few-public-methods # simplicity is good.
    """
    Define basic class for libpdf text classes.

    This class is inherited by :class:`~libpdf.models.horizontal_box.Word`,
    :class:`~libpdf.models.horizontal_box.HorizontalLine`, and :class:`~libpdf.models.horizontal_box.HorizontalBox`.

    The definition of text classes is the classes contains more than one character.
    """

    @property
    def bbox(self):
        """Obtain the rectangle coordinates from a list of libpdf text objects."""
        libpdf_text_objs = []
        if hasattr(self, 'chars'):
            libpdf_text_objs = self.chars  # pylint: disable=no-member # It comes when it has been inherited.
        elif hasattr(self, 'words'):
            words = self.words  # pylint: disable=no-member # It comes when it has been inherited.
            libpdf_text_objs.extend([char for word in words for char in word.chars])
        elif hasattr(self, 'lines'):
            words = []
            lines = self.lines  # pylint: disable=no-member # It comes when it has been inherited.
            words.extend([word for line in lines for word in line.words])
            libpdf_text_objs.extend([char for word in words for char in word.chars])

        if libpdf_text_objs:
            x0 = min(text_obj.x0 for text_obj in libpdf_text_objs)
            y0 = min(text_obj.y0 for text_obj in libpdf_text_objs)
            x1 = max(text_obj.x1 for text_obj in libpdf_text_objs)
            y1 = max(text_obj.y1 for text_obj in libpdf_text_objs)

            return {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}
        return None


class Char(Coord):  # pylint: disable=too-few-public-methods # simplicity is good.
    """
    Define the character class.

    :ivar text: plain text of the chararcter
    :vartype text: str
    :ivar x0: distance from the left of the page to the left edge of the character
    :vartype x0: float
    :ivar y0: distance from the bottom of the page to the lower edge of the character (less than y1)
    :vartype y0: float
    :ivar x1: distance from the left of the page to the right edge of the character
    :vartype x1: float
    :ivar y1: distance from the bottom of the page to the upper edge of the character (greater than y0)
    :vartype y1: float
    """

    def __init__(
        self,
        text: str,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ):
        """Init the class with plain text of a character and its rectangular coordinates."""
        super().__init__(x0=x0, y0=y0, x1=x1, y1=y1)
        self.text = text

    def __repr__(self):
        """Make the text part of the repr for better debugging."""
        return f'{self.text}'


class Word(TextBase):
    """
    Define the word class.

    A word shall contain several characters.

    :ivar chars: a list of the chararcter
    :vartype chars: List[Char]
    """

    def __init__(
        self,
        chars: List[Char],
    ):
        """Init the class with plain text of a word and its rectangular coordinates."""
        self.chars = chars

    @property
    def text(self):
        """Return plain text of a list of chararcters."""
        return ''.join([x.text for x in self.chars])

    def __repr__(self):
        """Make the text part of the repr for better debugging."""
        return f'{type(self).__name__}({self.text})'


class HorizontalLine(TextBase):
    """
    Define the horizontal line class.

    A horizontal line shall contain a word or several words.

    :ivar words: a list of the words
    :vartype words: List[Word]
    """

    def __init__(
        self,
        words: List[Word],
    ):
        """Init the class with plain text of a horizontal line and its rectangular coordinates."""
        self.words = words

    @property
    def text(self):
        """Return plain text of a list of chararcters."""
        return ' '.join([x.text for x in self.words])

    def __repr__(self):
        """Make the text part of the repr for better debugging."""
        return f'{type(self).__name__}({self.text})'


class HorizontalBox(TextBase):
    """
    Define the horizontal box class.

    A horizontal box shall contain a horizontal line or several of it.

    :ivar lines: a list of the HorizontalLine
    :vartype lines: List[HorizontalLine]
    """

    def __init__(
        self,
        lines: List[HorizontalLine],
    ):
        """Init the class with plain text of a horizontal box and its rectangular coordinates."""
        self.lines = lines

    @property
    def text(self):
        """Return plain text of a list of chararcters."""
        return '\n'.join([x.text for x in self.lines])

    def __repr__(self):
        """Make the text part of the repr for better debugging."""
        if self.lines:
            return f'{type(self).__name__}({self.text})'
        return None
