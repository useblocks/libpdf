"""Functional tests for PDFs in pdf folder."""

from datetime import datetime

from libpdf import load
from libpdf.models.chapter import Chapter
from libpdf.models.file import File, FileMeta
from libpdf.models.page import Page
from libpdf.models.paragraph import Paragraph
from libpdf.models.position import Position
from libpdf.models.root import Root
from libpdf.models.table import Cell, Table

from tests.conftest import PDF_LOREM_IPSUM


def test_lorem_ipsum():
    """Test if the library reads all content from input PDF correctly."""
    file = File(name='lorem-ipsum.pdf', path='/home/marco/ub/libpdf/tests/pdf/lorem-ipsum.pdf', page_count=2)
    file_meta = FileMeta(
        author=None,
        title=None,
        subject=None,
        creator='LaTeX with hyperref package',
        producer='pdfTeX-1.40.16',
        keywords=None,
        creation_date=datetime(2017, 5, 9, 13, 57, 58),
        modified_date=datetime(2017, 5, 9, 13, 57, 58),
        trapped=False,
    )
    file.file_meta = file_meta
    # file_meta.b_file = file  # does not yet work because field is missing
    root = Root(file=file, pages=[], content=[])

    # reverse engineer content to make full comarison
    # create object first
    dummy_page = Page(1, 700, 900)
    dummy_pos = Position(10, 10, 20, 20, dummy_page)
    dummy_links = []
    cell1_1 = Cell(1, 1, 'Tempora co Voluptatem', dummy_pos, dummy_links)
    cell2_6 = Cell(2, 6, 'Sed non ei Velit numq', dummy_pos, dummy_links)
    cell6_2 = Cell(6, 2, 'Etincidunt Consectetu', dummy_pos, dummy_links)
    cell18_7 = Cell(18, 7, 'Sit adipis', dummy_pos, dummy_links)
    table1 = Table(idx=1, cells=[cell1_1, cell2_6, cell6_2, cell18_7], position=dummy_pos)
    paragraph1 = Paragraph(
        idx=1,
        text='Labore ipsum sit est. Ipsum quisquam adipisci sed dolor sed. Non voluptatem voluptatem labore. Magnam '
        'quiquia neque consectetur amet non. Ut aliquam est quiquia dolor non. Quisquam ut etincidunt ipsum amet '
        'sed. Numquam labore consectetur dolorem non consectetur eius.',
        links=dummy_links,
        position=dummy_pos,
    )
    chapter1 = Chapter(title='Ipsum labore ut consectetur.', number='1', position=dummy_pos)
    chapter2 = Chapter(title='Quiquia adipisci numquam tempora dolore magnam.', number='2', position=dummy_pos)
    chapter2_1 = Chapter(title='Etincidunt consectetur porro velit sed quaerat.', number='2.1', position=dummy_pos)

    # create the right, ordered structure
    chapter2.content.append(chapter2_1)  # chapter2_1 is below chapter2
    root.content.append(table1)  # comes first
    root.content.append(paragraph1)  # comes before first chapter
    root.content.append(chapter1)
    root.content.append(chapter2)

    # load PDF
    objects = load(PDF_LOREM_IPSUM)
    del objects  # make pylint happy until implementation is finished

    # compare properties
