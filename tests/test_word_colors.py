"""Test catalog extraction."""

import logging

import libpdf
from tests.conftest import PDF_OUTLINE_NO_DEST


def test_word_color_chapter() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_OUTLINE_NO_DEST)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if chapter.title == "Create Basic Shapes":
            for content in chapter.content:
                if content.type == "paragraph" and "Diamond" in content.textbox.text:
                    words = content.textbox.words
                    logging.debug("found words ", words)
                    for word in words:
                        assert word.ncolor == (0, 0, 1)
