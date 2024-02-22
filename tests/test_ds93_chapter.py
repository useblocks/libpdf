"""Test case for JIRA ticket DS-93."""

import libpdf
from tests.conftest import PDF_CHAPTER_DETECTION


def test_chapter_detection():
    """
    Check if chapter detection is correct for 100% similarity textbox matches.

    That is the outline title is identical to a textbox containing both number and title.
    """
    objects = libpdf.load(PDF_CHAPTER_DETECTION)
    chapters = objects.flattened.chapters

    # check chapter numbers
    assert len(chapters) == 2

    # check chapter number and title
    # First chapter is "3.5.4 Franca-to-AUTOSAR Client Server Link"
    assert chapters[0].title == "Franca-to-AUTOSAR Client Server Link"
    assert chapters[0].number == "3.5.4"

    # Second chapter is "9. The note composition of C Chord are C, E and G"
    assert chapters[1].title == "The note composition of C Chord are C, E and G"
    assert chapters[1].number == "9."
