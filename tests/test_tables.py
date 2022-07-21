"""Test tables extraction."""

import libpdf

from tests.conftest import PDF_LOREM_IPSUM


def test_table_cells_words():
    """Check if tables extract cells words correctly."""
    objects = libpdf.load(PDF_LOREM_IPSUM)
    assert objects.flattened.tables is not None

    # check table 1 on page 1
    table_1 = objects.flattened.tables[0]
    assert table_1.uid == 'table.1'
    assert table_1.position.page.id_ == 'page.1'

    # check table 1 cell(1, 1)
    cell_1_1 = table_1.cells[0]
    assert cell_1_1.row == 1
    assert cell_1_1.col == 1
    assert cell_1_1.textbox.text == 'Tempora co\nVoluptatem'

    # check table 1 cell(3, 5)
    cell_3_5 = table_1.cells[14]
    assert cell_3_5.row == 3
    assert cell_3_5.col == 5
    assert cell_3_5.textbox.text == 'Eius quaer Etincidunt'
