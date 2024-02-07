"""Initial test cases for CLI."""
import pytest
from click.testing import CliRunner

from libpdf.core import main_cli
from tests.conftest import PDF_LOREM_IPSUM, PDF_TWO_COLUMNS


@pytest.mark.parametrize(
    "path",
    [PDF_LOREM_IPSUM, PDF_TWO_COLUMNS],
)
def test_cli_ok(path):
    """Check if CLI exits with code 0 when no errors occur."""
    runner = CliRunner()
    result = runner.invoke(
        main_cli, [str(path.absolute()), "-o", "out.yaml", "-f", "yaml"]
    )
    assert result.exception is None
    assert result.exit_code == 0
