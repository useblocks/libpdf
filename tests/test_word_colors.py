"""Test catalog extraction."""


import libpdf
from tests.conftest import PDF_COLOR_STYLE


def test_colors_0() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if chapter.title == "Color in Text and Heading":
            assert chapter.textbox.ncolor == (1, 0, 0)


def test_colors_1() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if chapter.title == "HorizontalLine":
            for content in chapter.content:
                if (
                    content.type == "paragraph"
                    and "Paragraph text is blue" in content.textbox.text
                ):
                    assert content.textbox.ncolor == (0, 0, 1)
                if (
                    content.type == "paragraph"
                    and "This chapter is for" in content.textbox.text
                ):
                    assert content.textbox.ncolor == (0, 0, 0)


def test_colors_2() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if chapter.title == "HorizontalBox":
            for content in chapter.content:
                if content.type == "paragraph":
                    assert content.textbox.ncolor == (0, 1, 0)
        elif chapter.title == "UncoloredHorizontalbox":
            for content in chapter.content:
                if content.type == "paragraph":
                    assert content.textbox.ncolor is None
                    for line in content.textbox.lines:
                        assert line.ncolor is not None


def test_colors_3() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if "Words" in chapter.title:
            for content in chapter.content:
                if (
                    content.type == "paragraph"
                    and "This line has no color" in content.textbox.text
                ):
                    assert content.textbox.ncolor is None

                    for word in content.textbox.words:
                        if word.text == "has":
                            assert word.ncolor == (0, 0, 1)
                        elif word.text == "color":
                            assert word.ncolor in [(0, 1, 0), (0, 0, 0)]
                        elif word.text == "changes":
                            assert word.ncolor == (1, 0, 0)
                        elif word.text == "words":
                            assert word.ncolor == (0, 0, 1)


def test_colors_4() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if "Words" in chapter.title:
            for content in chapter.content:
                if "This words have no color" in content.textbox.text:
                    assert content.textbox.ncolor is None

                    for word in content.textbox.words:
                        assert word.ncolor is None or word.ncolor == (0, 0, 0)


def test_colors_5() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if "Words" in chapter.title:
            for content in chapter.content:
                if "These words are printed" in content.textbox.text:
                    assert content.textbox.ncolor is None

                    for word in content.textbox.words:
                        if word.text in ["words", "but"]:
                            assert word.ncolor == (0, 1, 0)
                        elif word.text == "printed":
                            assert word.ncolor == (0, 0, 1)
                        elif word.text == "background":
                            assert word.ncolor == (1, 0, 0)


def test_colors_6() -> None:
    """Test word colors in given chapter paragraph."""
    objects = libpdf.load(PDF_COLOR_STYLE)
    assert objects is not None
    assert objects.flattened.chapters

    for chapter in objects.flattened.chapters:
        if "Styled Text" in chapter.title:
            for content in chapter.content:
                if "bold text format" in content.textbox.text:
                    assert content.textbox.bold is None
                    for word in content.textbox.words:
                        if word.text == "bold":
                            assert word.bold is True
                        else:
                            assert word.bold is False
                elif "italc text format" in content.textbox.text:
                    assert content.textbox.italic is None
                    if word.text == "italc":
                        assert word.italic is True
                    else:
                        assert word.italic is False
                elif "underline text format" in content.textbox.text:
                    # this seems to be exracted as rect
                    pass
