"""Definition for PDF root element."""

from typing import List, Union

from libpdf.models.chapter import Chapter
from libpdf.models.figure import Figure
from libpdf.models.file import File
from libpdf.models.model_base import ModelBase
from libpdf.models.page import Page
from libpdf.models.paragraph import Paragraph
from libpdf.models.table import Table


class Root(ModelBase):
    """
    Main entry point to the :ref:`uml_pdf_model`.

    :ivar file: a File instance
    :vartype file: File
    :ivar pages: PDF pages
    :vartype pages: List[Page]
    :ivar content: PDF contents/payload, given as list containing instances of type
                   :class:`~libpdf.models.element.Element`
    :vartype content: List[Union[Chapter, Paragraph, Table, Figure]]
    """

    def __init__(
        self,
        file: File,
        pages: List[Page],
        content: List[Union[Chapter, Paragraph, Table, Figure]],
    ):
        """Create publicly accessible objects."""
        self.file: File = file
        self.pages = pages
        self.content = content
        self.set_backref()

    def set_backref(self):
        """Set b_root property on class members that are not None."""
        if self.file is not None:
            self.file.b_root = self
        if self.pages is not None:
            for page in self.pages:
                page.b_root = self
        if self.content is not None:
            for element in self.content:
                element.b_root = self
