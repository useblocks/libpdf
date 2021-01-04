"""Initial test cases for CLI."""
import sys

from click.testing import CliRunner

from libpdf.core import main_cli

import pytest

from tests.conftest import PDF_LOREM_IPSUM, PDF_TWO_COLUMNS


@pytest.mark.parametrize(
    'path',
    [PDF_LOREM_IPSUM, PDF_TWO_COLUMNS],
)
def test_cli_ok(path):
    """Check if CLI exits with code 0 when no errors occur."""
    runner = CliRunner()
    result = runner.invoke(main_cli, [path, '-o', 'out.yaml', '-f', 'yaml'])
    if sys.platform.startswith('win'):
        # TODO bug on Windows currently for PDF_TWO_COLUMNS:
        #      UnicodeEncodeError('charmap', '\uf0b7  8 1/2', 0, 1, 'character maps to <undefined>')
        assert isinstance(result.exception, UnicodeEncodeError)
    else:
        assert result.exception is None
    assert result.exit_code == 0
