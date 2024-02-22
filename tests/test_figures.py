"""Test figures extraction."""

from click.testing import CliRunner

import libpdf
from tests.conftest import (
    PDF_FIGURE_WITH_INVALID_BBOX,
    PDF_FIGURES_EXTRACTION,
    PDF_FULL_FEATURES,
)


def test_figures_extract_with_invalid_bbox():
    """Check if figures extraction correctly when figures have invalid bbox."""
    runner = CliRunner()
    result = runner.invoke(libpdf.core.main_cli, [str(PDF_FIGURE_WITH_INVALID_BBOX)])
    assert result.exit_code == 0

    objects = libpdf.load(PDF_FIGURE_WITH_INVALID_BBOX)
    assert objects is not None
    # extract figures only with valid bbox
    assert len(objects.pdfplumber.pages[0].figures) == 1
    assert objects.pdfplumber.pages[0].figures[0]["height"] == 0
    assert (
        objects.pdfplumber.pages[0].figures[0]["y0"]
        == objects.pdfplumber.pages[0].figures[0]["y1"]
    )

    assert len(objects.pdfplumber.pages[1].figures) == 1
    assert objects.pdfplumber.pages[1].figures[0]["height"] == 0
    assert (
        objects.pdfplumber.pages[1].figures[0]["y0"]
        == objects.pdfplumber.pages[1].figures[0]["y1"]
    )

    assert not objects.flattened.figures


def test_figures_extraction():
    """Remove figures, which are completely inside other figures, from extracted figures list."""
    objects = libpdf.load(PDF_FIGURES_EXTRACTION)
    assert objects.flattened.figures is not None

    assert len(objects.pdfplumber.figures) == 6
    assert len(objects.flattened.figures) == 2

    # filter figure with negative position, partially outside page
    assert objects.pdfplumber.figures[2]["x0"] < 0
    # check that figure exists no more
    assert objects.flattened.figures[0].position.x0 >= 0
    assert objects.flattened.figures[1].position.x0 >= 0

    # filter figures that are too small
    assert objects.pdfplumber.figures[4]["width"] < 15
    assert objects.pdfplumber.figures[4]["height"] < 15
    # check that figure exists no more
    for figure in objects.flattened.figures:
        assert figure.position.x1 - figure.position.x0 >= 15
        assert figure.position.y1 - figure.position.y0 >= 15

    # filter figures that are completely inside other figures
    assert objects.pdfplumber.figures[1]["x0"] > objects.pdfplumber.figures[0]["x0"]
    assert objects.pdfplumber.figures[1]["y0"] > objects.pdfplumber.figures[0]["y0"]
    assert objects.pdfplumber.figures[1]["x1"] < objects.pdfplumber.figures[0]["x1"]
    assert objects.pdfplumber.figures[1]["y1"] < objects.pdfplumber.figures[0]["y1"]
    # check that figure exists no more
    for figure in objects.flattened.figures:
        assert abs(float(objects.pdfplumber.figures[1]["x0"]) - figure.position.x0) > 1
        assert abs(float(objects.pdfplumber.figures[1]["y0"]) - figure.position.y0) > 1
        assert abs(float(objects.pdfplumber.figures[1]["x1"]) - figure.position.x1) > 1
        assert abs(float(objects.pdfplumber.figures[1]["y1"]) - figure.position.y1) > 1

    # filter figures that are partially overlap with other figure, remove the smaller figure
    assert objects.pdfplumber.figures[3]["x0"] < objects.pdfplumber.figures[5]["x0"]
    assert objects.pdfplumber.figures[3]["y0"] < objects.pdfplumber.figures[5]["y0"]
    assert objects.pdfplumber.figures[3]["x1"] < objects.pdfplumber.figures[5]["x1"]
    assert objects.pdfplumber.figures[3]["y1"] < objects.pdfplumber.figures[5]["y1"]
    assert (
        objects.pdfplumber.figures[3]["width"] * objects.pdfplumber.figures[3]["height"]
        < objects.pdfplumber.figures[5]["width"]
        * objects.pdfplumber.figures[5]["height"]
    )
    # check that figure exists no more
    for figure in objects.flattened.figures:
        assert abs(float(objects.pdfplumber.figures[3]["x0"]) - figure.position.x0) > 1
        assert abs(float(objects.pdfplumber.figures[3]["y0"]) - figure.position.y0) > 1
        assert abs(float(objects.pdfplumber.figures[3]["x1"]) - figure.position.x1) > 1
        assert abs(float(objects.pdfplumber.figures[3]["y1"]) - figure.position.y1) > 1


def test_remove_figures_in_header_footer():
    """Remove figures that in header and footer."""
    objects = libpdf.load(PDF_FULL_FEATURES, smart_page_crop=True)
    assert len(objects.pdfplumber.figures) == 7
    assert len(objects.flattened.figures) == 2

    # on page 1, there are two figures, one is in header
    assert objects.pdfplumber.figures[0]["page_number"] == 1
    # figures[0] on page 1 is not in header
    assert float(objects.pdfplumber.figures[0]["y0"]) == 239.15
    assert float(objects.pdfplumber.figures[0]["y1"]) == 382.85
    # figures[1] on page 1 is in header
    assert objects.pdfplumber.figures[1]["page_number"] == 1
    assert float(objects.pdfplumber.figures[1]["y0"]) == 719.4
    assert float(objects.pdfplumber.figures[1]["y1"]) == 754.05

    # libpdf extract_figures removed that figure in header, only one figure left on page 1
    assert objects.flattened.figures[0].position.page.number == 1
    assert objects.flattened.figures[0].position.y0 == 239.15
    assert objects.flattened.figures[0].position.y1 == 382.85
