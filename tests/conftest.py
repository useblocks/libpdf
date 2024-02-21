"""Pytest conftest module containing common test configuration and fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libpdf.apiobjects import ApiObjects

import pytest

from libpdf import load

# test PDFs from pdfplumber
PDF_LOREM_IPSUM = Path(__file__).parent / "pdf" / "lorem-ipsum.pdf"
PDF_TWO_COLUMNS = Path(__file__).parent / "pdf" / "two_colums_sampe.pdf"
PDF_WITH_EMPTY_OUTLINE = Path(__file__).parent / "pdf" / "issue-67-example.pdf"

PDF_OUTLINE_NO_DEST = Path(__file__).parent / "pdf" / "pdffill-demo.pdf"
PDF_FIGURE_WITH_INVALID_BBOX = Path(__file__).parent / "pdf" / "pr-138-example.pdf"
PDF_CHAPTER_DETECTION = Path(__file__).parent / "pdf" / "DS93-chapter-issue-fix.pdf"

# full features PDF
PDF_FULL_FEATURES = Path(__file__).parent / "pdf" / "full_features.pdf"
PDF_FIGURES_EXTRACTION = Path(__file__).parent / "pdf" / "test_figures_extraction.pdf"
PDF_SMART_HEADER_FOOTER_DETECTION = (
    Path(__file__).parent / "pdf" / "test_header_footer_detection.pdf"
)

# test PDFs from official python documentation
PDF_PYTHON_LOGGING = Path(__file__).parent / "pdf" / "howto-logging.pdf"

# test PDF for rect extraction generateby by sphinx-simplepdf
PDF_RECTS_EXTRACTION = Path(__file__).parent / "pdf" / "test_rects_extraction.pdf"

# test PDF for color style info
PDF_COLOR_STYLE = Path(__file__).parent / "pdf" / "test_words_color_style.pdf"


@pytest.fixture(scope="session")
def load_full_features_pdf(
    tmpdir_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
) -> tuple(str, ApiObjects | None):
    """Load test pdf and return temporary directory path and the libpdf object."""
    tmpdir = tmpdir_factory.mktemp("full_features_pdf")
    tmpdir_path = str(tmpdir)
    save_figures = request.param if hasattr(request, "param") else False
    return tmpdir_path, load(
        PDF_FULL_FEATURES,
        save_figures=save_figures,
        figure_dir=Path(tmpdir_path) / "figures",
    )
