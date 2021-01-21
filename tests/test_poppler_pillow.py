"""Test case for Github Actions to test the poppler/pillow solution on all OS and Python versions."""


def test_run_poppler_pillow_example():
    """Import executes the code directly."""
    from examples import poppler_pillow  # pylint: disable=import-outside-toplevel
    del poppler_pillow
