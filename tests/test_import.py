"""Import tests."""


def test_import():
    """Check if the app modules can be imported."""
    from libpdf import core  # pylint: disable=import-outside-toplevel

    del core
