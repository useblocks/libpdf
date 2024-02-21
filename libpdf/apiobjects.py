"""Modules defines extracted object instances."""

from typing import List, NamedTuple

from pdfminer.pdfdocument import PDFDocument
from pdfplumber.pdf import PDF

from libpdf.models.chapter import Chapter
from libpdf.models.figure import Figure
from libpdf.models.paragraph import Paragraph
from libpdf.models.rect import Rect
from libpdf.models.root import Root
from libpdf.models.table import Table


# disable too-few-public-methods because this is a data storage class
# another option is using a dict but this does not feature IDE type hinting
class ApiObjects:  # pylint: disable = too-few-public-methods
    """
    Data class that stores instances for all extracted PDF objects.

    :ivar root: Main entry point to structured data as per the :ref:`uml_pdf_model`.
    :vartype root: Root
    :ivar flattened: named tuple holding flattened versions of all nested objects in root.contents.*;
                     the element types chapters/paragraphs/tables/figures can be directly accessed (API convenience)
    :vartype flattened: Flattened
    :ivar pdfplumber: pdfplumber PDF object for further processing by API users
    :vartype pdfplumber: PDF
    :ivar pdfminer: pdfminer PDF object for further processing by API users, also available in pdfplumber.doc
    :vartype pdfminer: PDFDocument
    """

    def __init__(  # pylint: disable=too-many-arguments  # the parameters are needed to describe in Sphinx autodoc
        self,
        root: Root,
        chapters: List[Chapter],
        paragraphs: List[Paragraph],
        tables: List[Table],
        figures: List[Figure],
        rects: List[Rect],
        pdfplumber: PDF,
        pdfminer: PDFDocument,
    ):
        """Create publicly accessible objects."""
        # main entry point to structured data
        self.root = root

        # attributes for API convenience
        self.flattened = Flattened(
            chapters=chapters,
            paragraphs=paragraphs,
            tables=tables,
            figures=figures,
            rects=rects,
        )

        # exposing the pdfplumber PDF object
        self.pdfplumber = pdfplumber

        # exposing the pdfminer PDF object
        if pdfminer is not None:
            # take argument first
            self.pdfminer = pdfminer
        elif pdfplumber is not None:
            # set from pdfplumber document
            self.pdfminer = pdfplumber.doc
        else:
            # nothing available
            self.pdfminer = None


class Flattened(NamedTuple):
    """NamedTuple to hold flattened Element instances featuring also type hinting."""

    chapters: List[Chapter]
    paragraphs: List[Paragraph]
    tables: List[Table]
    figures: List[Figure]
    rects: List[Rect]
