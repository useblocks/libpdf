"""Test catalog extraction."""
from click.testing import CliRunner

import libpdf

from tests.conftest import PDF_OUTLINE_NO_DEST, PDF_WITH_EMPTY_OUTLINE


def test_catalog_with_empty_outline():
    """Check if catalog extracted correctly with pdf that has empty outline."""
    runner = CliRunner()
    result = runner.invoke(libpdf.core.main_cli, [PDF_WITH_EMPTY_OUTLINE])
    assert result.exit_code == 0

    objects = libpdf.load(PDF_WITH_EMPTY_OUTLINE)
    assert objects is not None
    # extracted chapters should be empty if pdf has empty outline
    assert not objects.flattened.chapters


def test_catalog_outline_no_dest():
    """Check if catalog outline extraction correctly when pdf outline no destination to jump to."""
    objects = libpdf.load(PDF_OUTLINE_NO_DEST)
    assert objects is not None
    assert objects.flattened.chapters
    # outline without destination to jump to in this pdf will not be extracted as chapter
    assert len(objects.flattened.chapters) == 11
    assert objects.flattened.chapters[-1].title == 'Create Curves'
