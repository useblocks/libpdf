"""Definition of HorizontalBox to contain text in the PDF."""

from __future__ import annotations


class Char:  # pylint: disable=too-few-public-methods # simplicity is good.
    """
    Define the character class.

    :ivar ~.text: a plain char of the chararcter
    :vartype text: str
    :ivar x0: distance from the left of the page to the left edge of the character
    :vartype x0: float
    :ivar y0: distance from the bottom of the page to the lower edge of the character
        (less than y1)
    :vartype y0: float
    :ivar x1: distance from the left of the page to the right edge of the character
    :vartype x1: float
    :ivar y1: distance from the bottom of the page to the upper edge of the character
        (greater than y0)
    :vartype y1: float
    :ivar ncolor: non-stroking-color as rgb value
    :vartype ncolor: Tuple[float, float, float]
    """

    def __init__(
        self,
        text: str,
        x0: float | None = None,
        y0: float | None = None,
        x1: float | None = None,
        y1: float | None = None,
        ncolor: tuple | None = None,
        fontname: str = None,
    ):
        """Init with plain char of a character and its rectangular coordinates."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.text = text
        self.ncolor = ncolor
        self.fontname = fontname

    def __repr__(self) -> str:
        """Make the text part of the repr for better debugging."""
        return f"{type(self).__name__}({self.text})"


class Word:
    """
    Define the word class.

    A word shall contain several characters.

    :ivar chars: a list of the chararcter
    :vartype chars: List[Char]
    """

    def __init__(
        self,
        chars: list[Char],
        x0: float | None = None,
        y0: float | None = None,
        x1: float | None = None,
        y1: float | None = None,
    ):
        """Init the class with plain text of a word and its rectangular coordinates."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.chars = chars
        self.ncolor = None
        self.fontname = None

        if self.chars:
            # Obtain the rectangle coordinates from a list of libpdf text objects
            self.x0 = min(text_obj.x0 for text_obj in self.chars)
            self.y0 = min(text_obj.y0 for text_obj in self.chars)
            self.x1 = max(text_obj.x1 for text_obj in self.chars)
            self.y1 = max(text_obj.y1 for text_obj in self.chars)

            for n in ["ncolor", "fontname"]:
                if all(
                    getattr(x, n) == getattr(self.chars[0], n)
                    and getattr(x, n) is not None
                    for x in self.chars
                ):
                    setattr(self, n, getattr(self.chars[0], n))


==== BASE ====
    @property
    def text(self) -> str:
        """Return plain text."""
        return "".join([x.text for x in self.chars])

    def __repr__(self) -> str:
        """Make the text part of the repr for better debugging."""
        return f"{type(self).__name__}({self.text})"


class HorizontalLine:
    """
    Define the horizontal line class.

    A horizontal line shall contain a word or several words.

    :ivar words: a list of the words
    :vartype words: List[Word]
    """

    def __init__(
        self,
        words: list[Word],
        x0: float | None = None,
        y0: float | None = None,
        x1: float | None = None,
        y1: float | None = None,
    ):
        """Init with plain text of a horizontal line and its rectangular coordinates."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.words = words
        self.ncolor = None
        self.fontname = None

        if self.words:
            # Obtain the rectangle coordinates from a list of libpdf text objects
            self.x0 = min(text_obj.x0 for text_obj in self.words)
            self.y0 = min(text_obj.y0 for text_obj in self.words)
            self.x1 = max(text_obj.x1 for text_obj in self.words)
            self.y1 = max(text_obj.y1 for text_obj in self.words)

            for n in ["ncolor", "fontname"]:
                if all(
                    getattr(x, n) == getattr(self.words[0], n)
                    and getattr(x, n) is not None
                    for x in self.words
                ):
                    setattr(self, n, getattr(self.words[0], n))

    @property
    def text(self) -> str:
        """Return plain text."""
        return " ".join([x.text for x in self.words])

    def __repr__(self) -> str:
        """Make the text part of the repr for better debugging."""
        return f"{type(self).__name__}({self.text})"


class HorizontalBox:
    """
    Define the horizontal box class.

    A horizontal box shall contain a horizontal line or several of it.

    :ivar lines: a list of the HorizontalLine
    :vartype lines: List[HorizontalLine]
    """

    def __init__(
        self,
        lines: list[HorizontalLine],
        x0: float | None = None,
        y0: float | None = None,
        x1: float | None = None,
        y1: float | None = None,
    ):
        """Init with plain text of a horizontal box and its rectangular coordinates."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.lines = lines
        self.ncolor = None
        self.fontname = None

        if self.lines:
            # Obtain the rectangle coordinates from a list of libpdf text objects.
            self.x0 = min(text_obj.x0 for text_obj in self.lines)
            self.y0 = min(text_obj.y0 for text_obj in self.lines)
            self.x1 = max(text_obj.x1 for text_obj in self.lines)
            self.y1 = max(text_obj.y1 for text_obj in self.lines)

            _words = [word for line in self.lines for word in line.words]

            for n in ["ncolor", "fontname"]:
                if all(
                    getattr(x, n) == getattr(_words[0], n) and getattr(x, n) is not None
                    for x in _words
                ):
                    setattr(self, n, getattr(_words[0], n))

    @property
    def text(self) -> str:
        """Return plain text."""
        return "\n".join([x.text for x in self.lines])

    @property
    def words(self):
        """Return list of words"""
        return [word for line in self.lines for word in line.words]

    def __repr__(self) -> str | None:
        """Make the text part of the repr for better debugging."""
        if self.lines:
            return f"{type(self).__name__}({self.text})"
        return None
