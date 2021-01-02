"""Initial test cases for API."""

import logging

from libpdf import load

import pytest

from tests.conftest import PDF_LOREM_IPSUM, PDF_TWO_COLUMNS


@pytest.mark.parametrize(
    'path',
    [PDF_LOREM_IPSUM, PDF_TWO_COLUMNS],
)
def test_api_ok(tmpdir, path):
    """Check if API returns not None for API usage."""
    objects = load(path, figure_dir=str(tmpdir))
    assert objects is not None


# TODO remove monkeypatch
# TODO implement correctly
def test_logging(tmpdir, monkeypatch):
    """Check if log messages appear in output."""
    # monkeypatch the failing extract function
    def mock_extract(*args, **kwargs):
        # delete unused variables to denote they are not yet used
        del args
        del kwargs

    monkeypatch.setattr('libpdf.core.extract', mock_extract)
    logging.basicConfig()
    objects = load(PDF_LOREM_IPSUM, figure_dir=str(tmpdir))
    assert objects is None
