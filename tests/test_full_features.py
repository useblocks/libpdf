"""Full feature test cases for API."""

import os
import sys

import libpdf
from libpdf.models.figure import Figure
from libpdf.models.table import Table

import pytest

from tests.conftest import PDF_FULL_FEATURES, PDF_SMART_HEADER_FOOTER_DETECTION


def test_chapters(load_full_features_pdf):
    """Check if API extract all the chapters."""
    _, objects = load_full_features_pdf
    chapters = objects.flattened.chapters
    assert chapters is not None
    # check chapter numbers
    assert len(chapters) == 8

    # check chapter title
    # first 2 chapters have no number in PDF, so a virtual number is generated considering the chapter nesting
    assert chapters[0].title == 'Disclaimer'
    assert chapters[0].number == 'virt.1'
    assert chapters[1].title == 'Content of table'
    assert chapters[1].number == 'virt.1.1'

    # the following chapters have numbers
    assert chapters[2].title == 'Introduction'
    assert chapters[2].number == '1'
    assert chapters[3].title == 'Chapter Useful'
    assert chapters[3].number == '2'
    assert chapters[4].title == 'Meaningful'
    assert chapters[4].number == '2.1'
    assert chapters[5].title == 'Funny'
    assert chapters[5].number == '2.2'
    assert chapters[6].title == 'Surprise'
    assert chapters[6].number == '3'
    assert chapters[7].title == 'Example'
    assert chapters[7].number == 'A'

    # check chapter unique id
    assert chapters[0].uid == 'chapter.virt.1'
    assert chapters[1].uid == 'chapter.virt.1/chapter.virt.1.1'
    assert chapters[2].uid == 'chapter.1'
    assert chapters[3].uid == 'chapter.2'
    assert chapters[4].uid == 'chapter.2/chapter.2.1'
    assert chapters[5].uid == 'chapter.2/chapter.2.2'
    assert chapters[6].uid == 'chapter.3'
    assert chapters[7].uid == 'chapter.A'

    # check chapter headline position
    assert chapters[0].position.page.number == 1
    assert chapters[0].position.x0 > 56
    assert chapters[0].position.x1 < 149
    assert chapters[0].position.y0 > 173
    assert chapters[0].position.y1 < 192

    # check chapter content
    assert chapters[1].content is not None
    assert chapters[1].content[0].type == 'paragraph'
    assert chapters[1].content[0].text.startswith('libpdf allows the extraction')
    assert chapters[1].content[0].text.endswith('Figure or Table.')
    assert len(chapters[1].content[0].text.splitlines()) == 3


def test_tables(load_full_features_pdf):
    """Check if API extract all the tables."""
    _, objects = load_full_features_pdf
    tables = objects.flattened.tables
    assert tables is not None
    assert len(tables) == 2

    # check table type
    for table in tables:
        assert isinstance(table, Table)

    # check table location in pdf
    assert tables[0].position.page.number == 1
    assert tables[1].position.page.number == 5
    assert tables[1].position.x0 > 56
    assert tables[1].position.x1 < 300
    assert tables[1].position.y0 > 504
    assert tables[1].position.y1 < 654

    # check table content
    assert tables[1].cells[0].text == 'some'
    assert tables[1].columns[0][0] == tables[1].cells[0]
    assert tables[1].rows[2][1].text == 'Henry \ncavill'
    assert tables[1].rows[6][4].text == '3'

    # check table unique id
    assert tables[0].uid == 'table.1'
    assert tables[1].uid == 'chapter.3/table.1'


@pytest.mark.parametrize('load_full_features_pdf', [True], indirect=True)  # save figures
def test_figures(load_full_features_pdf):
    """Check if API extract all the figures."""
    tmpdir_path, objects = load_full_features_pdf
    figures = objects.flattened.figures
    assert figures is not None
    assert len(figures) == 7

    # check figure type
    for figure in figures:
        assert isinstance(figure, Figure)

    # check extracted figures stored location
    output_dir = os.path.join(tmpdir_path, 'figures')
    assert os.path.exists(output_dir)
    assert os.path.isdir(output_dir)
    # check output directory is not empty
    assert os.listdir(output_dir)
    assert len(os.listdir(output_dir)) == 7

    # check figure location in pdf
    assert figures[0].position.page.number == 1
    assert figures[1].position.page.number == 1
    assert figures[0].position.x0 > 200
    assert figures[0].position.x1 < 392
    assert figures[0].position.y0 > 239
    assert figures[0].position.y1 < 383
    # figures[1] in header
    assert figures[1].position.x0 > 73
    assert figures[1].position.x1 < 115
    assert figures[1].position.y0 > 719
    assert figures[1].position.y1 < 755

    # check figure unique id
    assert figures[0].uid == 'figure.1'
    # figure.2 is header figure
    assert figures[1].uid == 'figure.2'
    assert figures[2].uid == 'chapter.1/figure.1'


def test_content_structure(load_full_features_pdf):
    """Check pdf root content structure."""
    _, objects = load_full_features_pdf
    root = objects.root
    assert root is not None
    assert root.content is not None

    # 5 nested chapters and 9 content before first chapter
    assert len(root.content) == 14

    # content before first chapter
    assert root.content[0].type == 'paragraph'
    assert root.content[1].type == 'figure'
    assert root.content[4].type == 'table'
    assert root.content[7].type == 'figure'

    # chapter Useful contains two sub-chapters
    assert root.content[11].title == 'Chapter Useful'
    assert root.content[11].content[0].title == 'Meaningful'
    assert root.content[11].content[1].title == 'Funny'

    # sub-chapter contains a list of paragraphs, tables and figures including header/footer
    assert len(root.content[11].content[0].content) == 8
    assert root.content[11].content[0].content[0].type == 'paragraph'
    assert root.content[11].content[0].content[7].text == 'Release snyder cut of justice league!!!'

    # check paragraph unique id
    assert root.content[0].uid == 'paragraph.1'
    assert root.content[10].content[1].uid == 'chapter.1/paragraph.2'
    assert root.content[11].content[0].content[0].uid == 'chapter.2/chapter.2.1/paragraph.1'
    assert root.content[13].content[0].uid == 'chapter.A/paragraph.1'

    # check paragraphs amounts
    assert len(objects.flattened.paragraphs) == 48


def test_smart_header_footer_detection():
    """Check smart header/footer detection."""
    objects = libpdf.load(PDF_FULL_FEATURES, smart_page_crop=True)

    # check smart header/footer detection only remove paragraphs/figures/tables in header/footer
    assert len(objects.flattened.figures) == 2
    # on page 1 and page 2 only 1 figure left and header figure is removed
    assert objects.flattened.figures[0].position.page.number == 1
    assert objects.flattened.figures[0].uid == 'figure.1'
    assert objects.flattened.figures[0].position.x0 > 200
    assert objects.flattened.figures[0].position.x1 < 392
    assert objects.flattened.figures[0].position.y0 > 239
    assert objects.flattened.figures[0].position.y1 < 383

    assert objects.flattened.figures[1].position.page.number == 2
    assert objects.flattened.figures[1].uid == 'chapter.1/figure.1'

    assert len(objects.flattened.tables) == 2

    # 10 paragraphs in header/footer
    assert len(objects.flattened.paragraphs) == 38
    assert objects.flattened.paragraphs[0].uid == 'paragraph.2'
    assert objects.flattened.paragraphs[0].text.startswith('libpdf allows the extraction')

    # Check smart header/footer detection for pdf without outline
    objects = libpdf.load(PDF_SMART_HEADER_FOOTER_DETECTION)
    assert len(objects.flattened.paragraphs) == 42

    # check smart header/footer detection doesn't remove paragraphs when they are close to
    # header/footer and at similar location
    smart_objects = libpdf.load(PDF_SMART_HEADER_FOOTER_DETECTION, smart_page_crop=True)
    assert len(smart_objects.flattened.paragraphs) == 30
    assert smart_objects.flattened.paragraphs[0].text == '1. Chapter title for header'
    assert smart_objects.flattened.paragraphs[12].text == '1. Chapter test for footer'
    assert smart_objects.flattened.paragraphs[13].text == '2. Chapter title for header'
    assert smart_objects.flattened.paragraphs[17].text == '2. Chapter test for footer'
    assert smart_objects.flattened.paragraphs[18].text == '3. Chapter title for header'
    assert smart_objects.flattened.paragraphs[23].text == '3. Chapter test for footer'
    assert smart_objects.flattened.paragraphs[24].text == '4. Chapter title for header'
    assert smart_objects.flattened.paragraphs[29].text == '4. Chapter test for footer'


@pytest.mark.skipif(sys.platform.startswith('win'), reason='visual debugging: ImageMagick not installed on Win')
def test_visual_debug_include_elements(tmpdir):
    """Test visual debug include visualized elements."""
    visual_debug_output_dir = os.path.join(tmpdir, 'visual_debug_libpdf')
    libpdf.load(
        PDF_FULL_FEATURES,
        visual_debug=True,
        visual_debug_output_dir=visual_debug_output_dir,
        visual_split_elements=True,
        visual_debug_include_elements=['chapter'],
    )
    # check visual debug output directory
    assert os.path.exists(visual_debug_output_dir)
    assert os.path.isdir(visual_debug_output_dir)

    # check visual debug included elements directory exist
    included_elements_dir = os.path.join(visual_debug_output_dir, 'chapter')
    assert os.path.exists(included_elements_dir)
    assert os.path.isdir(included_elements_dir)
    # check only one visual debug element directory
    assert len(os.listdir(visual_debug_output_dir)) == 1


@pytest.mark.skipif(sys.platform.startswith('win'), reason='visual debugging: ImageMagick not installed on Win')
def test_visual_debug_exclude_elements(tmpdir):
    """Test visual debug exclude visualized elements."""
    visual_debug_output_dir = os.path.join(tmpdir, 'visual_debug_libpdf')
    libpdf.load(
        PDF_FULL_FEATURES,
        visual_debug=True,
        visual_debug_output_dir=visual_debug_output_dir,
        visual_split_elements=True,
        visual_debug_exclude_elements=['chapter', 'figure'],
    )
    # check visual excluded elements directory not exist
    excluded_elements_figure_dir = os.path.join(visual_debug_output_dir, 'figure')
    assert not os.path.exists(excluded_elements_figure_dir)

    excluded_elements_chapter_dir = os.path.join(visual_debug_output_dir, 'chapter')
    assert not os.path.exists(excluded_elements_chapter_dir)

    # check visual debug visualized elements directory paragraph and table exist
    included_elements_paragraph_dir = os.path.join(visual_debug_output_dir, 'paragraph')
    assert os.path.exists(included_elements_paragraph_dir)
    assert os.path.isdir(included_elements_paragraph_dir)

    included_elements_table_dir = os.path.join(visual_debug_output_dir, 'table')
    assert os.path.exists(included_elements_table_dir)
    assert os.path.isdir(included_elements_table_dir)
