"""Libpdf exceptions."""


class LibpdfError(Exception):
    """Generic libpdf exception class."""


class TextContainsNewlineError(ValueError):
    """Text cannot contain newline character."""

    def __init__(self, text: str):
        super().__init__(f'Input text "{text}" contains a new line character.')
